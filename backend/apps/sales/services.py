from django.db import transaction
from apps.inventory.services import StockService
from apps.inventory.models import StockItem
from common.utils import log_audit
from .models import Cart, Order, OrderItem
from .integrations.stripe_payment import crear_intento_pago, verificar_pago, PagoRechazadoError


class CheckoutService:
    @staticmethod
    def iniciar_checkout(cliente, sucursal):
        """
        CU15 (paso 1) - Valida el carrito y stock, crea una Order en
        PENDIENTE (referencia_pago = id del PaymentIntent de Stripe) y
        devuelve el client_secret para que el frontend muestre el
        campo de tarjeta y confirme el cobro.
        """
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

        total = sum(item.id_variante.precio * item.cantidad for item in items)

        try:
            payment_intent_id, client_secret = crear_intento_pago(total)
        except PagoRechazadoError as e:
            raise ValueError(f"No se pudo iniciar el pago: {e}")

        order = Order.objects.create(
            id_cliente=cliente,
            id_sucursal=sucursal,
            total=total,
            estado="PENDIENTE",
            metodo_pago="TARJETA",
            referencia_pago=payment_intent_id,
        )

        return order, client_secret

    @staticmethod
    @transaction.atomic
    def confirmar_pago(cliente, referencia_pago):
        """
        CU15 (paso 2) - El cliente ya confirmó la tarjeta en el
        navegador con Stripe.js. Verificamos server-to-server que
        Stripe efectivamente cobró, y recién ahí cerramos la orden:
        creamos los OrderItem, descontamos stock (cierra CU10) y
        marcamos el carrito como CONVERTIDO.
        """
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