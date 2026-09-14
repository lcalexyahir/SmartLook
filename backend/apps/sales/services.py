from django.db import transaction
from apps.inventory.services import StockService
from apps.inventory.models import StockItem
from common.utils import log_audit
from .models import Cart, Order, OrderItem
from .integrations.pasarela_pago import procesar_pago, PagoRechazadoError


class CheckoutService:
    @staticmethod
    @transaction.atomic
    def procesar_checkout(cliente, sucursal):
        cart = Cart.objects.select_for_update().filter(
            id_cliente=cliente, estado="ACTIVO"
        ).first()
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
            referencia_pago = procesar_pago(total)
        except PagoRechazadoError as e:
            raise ValueError(f"Pago rechazado: {e}")

        order = Order.objects.create(
            id_cliente=cliente,
            id_sucursal=sucursal,
            total=total,
            estado="PAGADA",
            metodo_pago="TARJETA",
            referencia_pago=referencia_pago,
        )
        for item in items:
            OrderItem.objects.create(
                id_orden=order,
                id_variante=item.id_variante,
                cantidad=item.cantidad,
                precio_unitario=item.id_variante.precio,
                subtotal=item.id_variante.precio * item.cantidad,
            )
            StockService.registrar_movimiento(
                sucursal=sucursal,
                variante=item.id_variante,
                usuario=cliente.id_usuario,
                tipo="SALIDA",
                cantidad=item.cantidad,
                motivo=f"Venta digital - Orden #{order.id_orden}",
            )

        cart.estado = "CONVERTIDO"
        cart.save()

        # NUEVO: registro legible en Bitácora, con nombre del cliente,
        # además del genérico que ya deja el AuditMiddleware.
        log_audit(
            usuario=cliente.id_usuario,
            accion="COMPRA_DIGITAL",
            tabla_afectada="orders",
            registro_id=order.id_orden,
            descripcion=(
                f"{cliente.id_usuario.nombres} {cliente.id_usuario.apellidos} "
                f"realizó una compra digital en {sucursal.nombre} - "
                f"Orden #{order.id_orden} - Bs {order.total}"
            ),
        )

        return order