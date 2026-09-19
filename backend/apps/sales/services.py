from decimal import Decimal

from django.db import transaction
from apps.inventory.services import StockService
from apps.inventory.models import StockItem
from apps.catalog.models import ProductoVariante
from common.utils import log_audit
from .models import Cart, Delivery, Order, OrderItem, PosSale, PosSaleItem
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

        items = list(cart.cartitem_set.select_related("id_variante"))

        for item in items:
            OrderItem.objects.create(
                id_orden=order,
                id_variante=item.id_variante,
                cantidad=item.cantidad,
                precio_unitario=item.id_variante.precio,
                subtotal=item.id_variante.precio * item.cantidad,
            )
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
        {"id_variante": <int>, "cantidad": <int>}. Valida stock,
        descuenta inventario (cierra CU10 para el flujo presencial)
        y crea PosSale + PosSaleItem, todo en una transacción.
        """
        if not items_data:
            raise ValueError("La venta debe tener al menos una prenda.")

        variantes = {}
        for item in items_data:
            try:
                variante = ProductoVariante.objects.get(pk=item["id_variante"])
            except ProductoVariante.DoesNotExist:
                raise ValueError(f"La prenda con id {item['id_variante']} no existe.")
            variantes[variante.id_variante] = variante

            stock = StockItem.objects.filter(id_sucursal=sucursal, id_variante=variante).first()
            if not stock or stock.cantidad < item["cantidad"]:
                raise ValueError(f"Stock insuficiente de '{variante}' en {sucursal.nombre}.")

        total = sum(
            variantes[item["id_variante"]].precio * item["cantidad"] for item in items_data
        )

        venta = PosSale.objects.create(
            id_sucursal=sucursal,
            id_usuario=cajero,
            total=total,
            metodo_pago=metodo_pago,
        )

        for item in items_data:
            variante = variantes[item["id_variante"]]
            PosSaleItem.objects.create(
                id_venta=venta,
                id_variante=variante,
                cantidad=item["cantidad"],
                precio_unitario=variante.precio,
                subtotal=variante.precio * item["cantidad"],
            )
            StockService.registrar_movimiento(
                sucursal=sucursal,
                variante=variante,
                usuario=cajero,
                tipo="SALIDA",
                cantidad=item["cantidad"],
                motivo=f"Venta presencial - Venta #{venta.id_venta}",
            )

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