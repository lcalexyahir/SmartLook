# backend/apps/sales/services.py
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from apps.inventory.services import StockService
from apps.inventory.models import StockItem
from apps.catalog.models import ProductoVariante
from common.utils import log_audit
from .models import Cart, Delivery, Order, OrderItem, PosSale, PosSaleItem, Devolucion, DevolucionItem
from .integrations.stripe_payment import crear_intento_pago, verificar_pago, PagoRechazadoError
from .integrations.envio import cotizar, EnvioError


class CheckoutService:
    @staticmethod
    def iniciar_checkout(cliente, sucursal, tipo_entrega="RETIRO", entrega=None):
        """
        tipo_entrega: "RETIRO" (el cliente recoge en la sucursal) o "DELIVERY".
        entrega (solo DELIVERY): {"direccion", "referencia", "latitud", "longitud"}.
        El costo de envío se calcula aquí, en el servidor.
        """
        if tipo_entrega not in ("RETIRO", "DELIVERY"):
            raise ValueError("Tipo de entrega inválido.")

        cart = Cart.objects.filter(id_cliente=cliente, estado="ACTIVO").first()
        if not cart or not cart.cartitem_set.exists():
            raise ValueError("El carrito está vacío.")

        items = list(cart.cartitem_set.select_related("id_variante"))

        for item in items:
            if item.id_reserva_item_id:
                continue
            stock = StockItem.objects.filter(
                id_sucursal=sucursal, id_variante=item.id_variante
            ).first()
            if not stock or stock.cantidad < item.cantidad:
                raise ValueError(
                    f"Stock insuficiente de '{item.id_variante}' en {sucursal.nombre}."
                )

        subtotal = sum(item.id_variante.precio * item.cantidad for item in items)
        costo_envio = Decimal("0.00")
        cotizacion = None

        if tipo_entrega == "DELIVERY":
            entrega = entrega or {}
            direccion = (entrega.get("direccion") or "").strip()
            if not direccion:
                raise ValueError("Debe indicar la dirección de entrega.")
            try:
                latitud = float(entrega.get("latitud"))
                longitud = float(entrega.get("longitud"))
            except (TypeError, ValueError):
                raise ValueError("Debe indicar la ubicación de entrega.")
            if not (-90 <= latitud <= 90 and -180 <= longitud <= 180):
                raise ValueError("La ubicación de entrega no es válida.")
            try:
                cotizacion = cotizar(
                    sucursal, latitud, longitud, sum(item.cantidad for item in items)
                )
            except EnvioError as e:
                raise ValueError(str(e))
            costo_envio = cotizacion["costo_envio"]

        total = subtotal + costo_envio

        try:
            payment_intent_id, client_secret = crear_intento_pago(total)
        except PagoRechazadoError as e:
            raise ValueError(f"No se pudo iniciar el pago: {e}")

        with transaction.atomic():
            order = Order.objects.create(
                id_cliente=cliente,
                id_sucursal=sucursal,
                total=total,
                estado="PENDIENTE",
                metodo_pago="TARJETA",
                referencia_pago=payment_intent_id,
                tipo_entrega=tipo_entrega,
                costo_envio=costo_envio,
            )
            if cotizacion:
                Delivery.objects.create(
                    id_orden=order,
                    direccion=direccion,
                    referencia=(entrega.get("referencia") or "").strip() or None,
                    latitud=Decimal(str(round(latitud, 6))),
                    longitud=Decimal(str(round(longitud, 6))),
                    distancia_km=cotizacion["distancia_km"],
                    costo_envio=costo_envio,
                )
        return order, client_secret

    @staticmethod
    @transaction.atomic
    def confirmar_pago(cliente, referencia_pago):
        order = Order.objects.select_for_update().filter(
            id_cliente=cliente, referencia_pago=referencia_pago, estado="PENDIENTE"
        ).first()
        if not order:
            raise ValueError("No se encontró una orden pendiente con esa referencia.")

        try:
            verificar_pago(referencia_pago)
        except PagoRechazadoError as e:
            raise ValueError(f"Pago rechazado: {e}")

        cart = Cart.objects.select_for_update().filter(
            id_cliente=cliente, estado="ACTIVO"
        ).first()
        if not cart or not cart.cartitem_set.exists():
            raise ValueError("El carrito ya no tiene items para completar la orden.")

        items = list(cart.cartitem_set.select_related("id_variante", "id_reserva_item"))

        items_reserva_comprados = []
        for item in items:
            OrderItem.objects.create(
                id_orden=order,
                id_variante=item.id_variante,
                cantidad=item.cantidad,
                precio_unitario=item.id_variante.precio,
                subtotal=item.id_variante.precio * item.cantidad,
            )
            if item.id_reserva_item_id:
                items_reserva_comprados.append(item.id_reserva_item)
            else:
                StockService.registrar_movimiento(
                    sucursal=order.id_sucursal,
                    variante=item.id_variante,
                    usuario=cliente.id_usuario,
                    tipo="SALIDA",
                    cantidad=item.cantidad,
                    motivo=f"Venta digital - Orden #{order.id_orden}",
                )

        order.estado = "PAGADA"
        order.save()
        cart.estado = "CONVERTIDO"
        cart.save()

        if items_reserva_comprados:
            from apps.reservations.services import ReservationStockService
            ReservationStockService.resolver_reserva_por_venta(
                items_reserva_comprados, cliente.id_usuario
            )

        log_audit(
            usuario=cliente.id_usuario,
            accion="COMPRA_DIGITAL",
            tabla_afectada="orders",
            registro_id=order.id_orden,
            descripcion=(
                f"{cliente.id_usuario.nombres} {cliente.id_usuario.apellidos} "
                f"realizó una compra digital en {order.id_sucursal.nombre} - "
                f"Orden #{order.id_orden} - Bs {order.total}"
            ),
        )
        return order


class PosSaleService:
    @staticmethod
    @transaction.atomic
    def registrar_venta(cajero, sucursal, items_data, metodo_pago):
        """
        CU16 - Registra una venta presencial. items_data: lista de
        {"id_variante": <int>, "cantidad": <int>} para prendas normales,
        o {"id_reserva_item": <int>, "cantidad": 1} para prendas que
        vienen de una reserva confirmada.
        """
        if not items_data:
            raise ValueError("La venta debe tener al menos una prenda.")

        from apps.reservations.models import FittingReservationItem
        from apps.reservations.services import ReservationStockService

        variantes = {}
        reserva_items = {}
        for item in items_data:
            id_reserva_item = item.get("id_reserva_item")
            if id_reserva_item:
                try:
                    ri = FittingReservationItem.objects.select_related(
                        "id_variante", "id_reserva"
                    ).get(pk=id_reserva_item, estado="PENDIENTE")
                except FittingReservationItem.DoesNotExist:
                    raise ValueError(
                        f"La prenda reservada con id {id_reserva_item} no existe o ya se resolvió."
                    )
                if ri.id_reserva.id_sucursal_id != sucursal.id_sucursal:
                    raise ValueError(
                        f"La reserva #{ri.id_reserva_id} no corresponde a {sucursal.nombre}."
                    )
                reserva_items[id_reserva_item] = ri
                continue

            try:
                variante = ProductoVariante.objects.get(pk=item["id_variante"])
            except ProductoVariante.DoesNotExist:
                raise ValueError(f"La prenda con id {item['id_variante']} no existe.")
            variantes[variante.id_variante] = variante

            stock = StockItem.objects.filter(id_sucursal=sucursal, id_variante=variante).first()
            if not stock or stock.cantidad < item["cantidad"]:
                raise ValueError(f"Stock insuficiente de '{variante}' en {sucursal.nombre}.")

        def _variante_de(item):
            if item.get("id_reserva_item"):
                return reserva_items[item["id_reserva_item"]].id_variante
            return variantes[item["id_variante"]]

        total = sum(_variante_de(item).precio * item.get("cantidad", 1) for item in items_data)

        venta = PosSale.objects.create(
            id_sucursal=sucursal,
            id_usuario=cajero,
            total=total,
            metodo_pago=metodo_pago,
        )

        items_reserva_comprados = []
        for item in items_data:
            variante = _variante_de(item)
            id_reserva_item = item.get("id_reserva_item")
            cantidad = item.get("cantidad", 1)

            PosSaleItem.objects.create(
                id_venta=venta,
                id_variante=variante,
                cantidad=cantidad,
                precio_unitario=variante.precio,
                subtotal=variante.precio * cantidad,
                id_reserva_item=reserva_items.get(id_reserva_item) if id_reserva_item else None,
            )

            if id_reserva_item:
                items_reserva_comprados.append(reserva_items[id_reserva_item])
            else:
                StockService.registrar_movimiento(
                    sucursal=sucursal,
                    variante=variante,
                    usuario=cajero,
                    tipo="SALIDA",
                    cantidad=cantidad,
                    motivo=f"Venta presencial - Venta #{venta.id_venta}",
                )

        if items_reserva_comprados:
            ReservationStockService.resolver_reserva_por_venta(items_reserva_comprados, cajero)

        log_audit(
            usuario=cajero,
            accion="VENTA_PRESENCIAL",
            tabla_afectada="pos_sale",
            registro_id=venta.id_venta,
            descripcion=(
                f"{cajero.nombres} {cajero.apellidos} registró una venta "
                f"presencial en {sucursal.nombre} - Venta #{venta.id_venta} - "
                f"Bs {venta.total} ({metodo_pago})"
            ),
        )
        return venta


# NUEVO (devoluciones): mensaje de disculpa que se le muestra al cliente
# según el motivo - vive en el backend para que web y mobile no tengan
# cada uno su propia copia del texto (una sola fuente de verdad).
MOTIVO_MENSAJES = {
    "TALLA_INCORRECTA": (
        "Lamentamos el inconveniente, nos equivocamos con la talla. Ya "
        "estamos solucionando esto y te contactaremos para coordinar el cambio."
    ),
    "COLOR_INCORRECTO": (
        "Lamentamos el inconveniente, nos equivocamos con el color. Ya "
        "estamos solucionando esto y te contactaremos para coordinar el cambio."
    ),
    "PRODUCTO_DANADO": (
        "Lamentamos que la prenda haya llegado dañada. Ya estamos "
        "solucionando esto y te contactaremos a la brevedad."
    ),
    "OTRO": (
        "Lamentamos el inconveniente. Ya estamos revisando tu caso y te "
        "contactaremos a la brevedad."
    ),
}


class DevolucionService:
    @staticmethod
    @transaction.atomic
    def solicitar_devolucion(cliente, orden, items_data):
        """
        Devolución de prendas de un pedido con delivery ya entregado (ej.
        la sucursal se equivocó de talla/color). items_data: lista de
        {"id_orden_item": <int>, "cantidad": <int>, "motivo": <str>}.

        Se completa sola (sin aprobación de un encargado): valida que la
        orden sea DELIVERY, esté ENTREGADA y sea del cliente, repone
        stock (ENTRADA) en la sucursal que despachó la orden por cada
        prenda devuelta, y devuelve los mensajes de disculpa según el
        motivo de cada una para mostrarlos directo en la app/web.
        """
        if orden.id_cliente_id != cliente.id_cliente:
            raise ValueError("Esta orden no te pertenece.")
        if orden.tipo_entrega != "DELIVERY":
            raise ValueError("Solo se pueden devolver pedidos con delivery.")
        if orden.estado != "ENTREGADA":
            raise ValueError("Solo se puede devolver un pedido ya entregado.")
        if not items_data:
            raise ValueError("Debe indicar al menos una prenda a devolver.")

        devolucion = Devolucion.objects.create(id_orden=orden, id_cliente=cliente)
        mensajes = []

        for item in items_data:
            try:
                orden_item = OrderItem.objects.select_related("id_variante").get(
                    pk=item.get("id_orden_item"), id_orden=orden
                )
            except OrderItem.DoesNotExist:
                raise ValueError(
                    f"La prenda con id {item.get('id_orden_item')} no pertenece a esta orden."
                )

            cantidad = int(item.get("cantidad") or 1)
            motivo = item.get("motivo")
            if motivo not in MOTIVO_MENSAJES:
                raise ValueError(f"Motivo de devolución inválido: {motivo}")
            if cantidad < 1:
                raise ValueError("La cantidad a devolver debe ser al menos 1.")

            ya_devuelto = DevolucionItem.objects.filter(
                id_orden_item=orden_item
            ).aggregate(total=Sum("cantidad"))["total"] or 0
            if ya_devuelto + cantidad > orden_item.cantidad:
                raise ValueError(
                    f"Ya devolviste {ya_devuelto} de {orden_item.cantidad} unidad(es) de "
                    f"'{orden_item.id_variante}'; no puedes devolver {cantidad} más."
                )

            DevolucionItem.objects.create(
                id_devolucion=devolucion,
                id_orden_item=orden_item,
                cantidad=cantidad,
                motivo=motivo,
            )

            StockService.registrar_movimiento(
                sucursal=orden.id_sucursal,
                variante=orden_item.id_variante,
                usuario=cliente.id_usuario,
                tipo="ENTRADA",
                cantidad=cantidad,
                motivo=f"Devolución Orden #{orden.id_orden} (Devolución #{devolucion.id_devolucion})",
            )

            mensajes.append(MOTIVO_MENSAJES[motivo])

        log_audit(
            usuario=cliente.id_usuario,
            accion="DEVOLUCION_SOLICITADA",
            tabla_afectada="devolucion",
            registro_id=devolucion.id_devolucion,
            descripcion=(
                f"{cliente.id_usuario.nombres} {cliente.id_usuario.apellidos} solicitó "
                f"una devolución de la Orden #{orden.id_orden} - Devolución #{devolucion.id_devolucion}"
            ),
        )

        return devolucion, mensajes