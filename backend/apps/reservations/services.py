# backend/apps/reservations/services.py
from django.db import transaction

from apps.inventory.models import StockItem
from apps.inventory.services import StockService


class ReservationStockError(Exception):
    """Se usa cuando una prenda de la reserva ya no tiene stock disponible."""


class ReservationStockService:
    """
    Conecta las reservas de probador (CU11/CU12/CU13) con el inventario
    real (CU10) y con las ventas (CU15/CU16/CU21).

    Reglas de negocio:
    - Reservar SÍ descuenta stock real (SALIDA).
    - Cancelar una reserva SÍ lo repone (ENTRADA).
    - Confirmar una reserva agrega sus prendas al carrito del cliente
      (no toca stock, ya se descontó al reservar) y las deja visibles
      para el punto de venta.
    - Pagar (por caja o digital) una prenda reservada NO vuelve a
      descontar su stock. Cualquier otra prenda de esa misma reserva que
      no se compró se repone sola y la reserva queda COMPLETADA.
    """

    # ---------- CU11: crear reserva ----------

    @staticmethod
    @transaction.atomic
    def reservar_items(reserva):
        """
        Descuenta stock (SALIDA, 1 unidad) para cada prenda de la
        reserva, en la sucursal de la reserva. Usa select_for_update()
        para que dos reservas simultáneas de la última unidad no puedan
        pasar la validación al mismo tiempo (la causa original del bug).
        Si alguna prenda ya no tiene stock suficiente, revierte todo
        (transaction.atomic) y lanza ReservationStockError.
        """
        for item in reserva.items.select_related("id_variante").all():
            stock_item, _ = StockItem.objects.select_for_update().get_or_create(
                id_sucursal=reserva.id_sucursal,
                id_variante=item.id_variante,
                defaults={"cantidad": 0},
            )

            if stock_item.cantidad < 1:
                raise ReservationStockError(
                    f"'{item.id_variante}' ya no tiene stock disponible en "
                    f"{reserva.id_sucursal.nombre}."
                )

            StockService.registrar_movimiento(
                sucursal=reserva.id_sucursal,
                variante=item.id_variante,
                usuario=reserva.id_cliente.id_usuario,
                tipo="SALIDA",
                cantidad=1,
                motivo=f"Reserva #{reserva.id_reserva} (vestidor)",
            )

    # ---------- liberar una prenda individual (pieza central) ----------

    @staticmethod
    @transaction.atomic
    def liberar_item(item, usuario, motivo):
        """
        Repone stock (ENTRADA, 1 unidad) de UNA prenda de una reserva que
        no se va a comprar (se quitó del carrito, se canceló la reserva,
        o quedó pendiente cuando se pagó el resto). Marca el item como
        DEVUELTO, borra cualquier CartItem que la tuviera vinculada (ya
        no es comprable) y, si con esto no queda ninguna prenda
        PENDIENTE en la reserva, la cierra sola como COMPLETADA.
        """
        if item.estado != "PENDIENTE":
            return

        from apps.sales.models import CartItem

        reserva = item.id_reserva

        StockService.registrar_movimiento(
            sucursal=reserva.id_sucursal,
            variante=item.id_variante,
            usuario=usuario,
            tipo="ENTRADA",
            cantidad=1,
            motivo=motivo,
        )
        item.estado = "DEVUELTO"
        item.save()
        CartItem.objects.filter(id_reserva_item=item).delete()

        if (
            not reserva.items.filter(estado="PENDIENTE").exists()
            and reserva.estado not in ("COMPLETADA", "CANCELADA")
        ):
            reserva.estado = "COMPLETADA"
            reserva.save()

    # ---------- CU12/CU13: cancelar reserva completa ----------

    @staticmethod
    @transaction.atomic
    def liberar_items(reserva, usuario):
        """
        Repone stock de todas las prendas PENDIENTES de una reserva que
        se cancela (las ya compradas o ya devueltas no se tocan).
        """
        for item in list(reserva.items.filter(estado="PENDIENTE")):
            ReservationStockService.liberar_item(
                item,
                usuario=usuario,
                motivo=f"Cancelación Reserva #{reserva.id_reserva} (vestidor)",
            )

    # ---------- CU12: confirmar reserva ----------

    @staticmethod
    @transaction.atomic
    def confirmar_reserva(reserva):
        """
        Al confirmar la reserva, sus prendas quedan disponibles para
        pagarse por dos caminos: se agregan al carrito del cliente
        (checkout digital / delivery, CU15/CU21) y quedan visibles para
        el punto de venta de esa sucursal (CU16, filtrando reservas
        CONFIRMADA por sucursal). El stock NO se toca aquí: ya se
        descontó al crear la reserva (CU11).
        """
        from apps.sales.models import Cart, CartItem

        cart, _ = Cart.objects.get_or_create(id_cliente=reserva.id_cliente, estado="ACTIVO")
        for item in reserva.items.filter(estado="PENDIENTE"):
            CartItem.objects.get_or_create(
                id_carrito=cart,
                id_reserva_item=item,
                defaults={"id_variante": item.id_variante, "cantidad": 1},
            )

    # ---------- CU15/CU16/CU21: se pagó/cobró una prenda reservada ----------

    @staticmethod
    @transaction.atomic
    def resolver_reserva_por_venta(items_reserva_comprados, usuario):
        """
        Se llama después de una venta (CheckoutService o PosSaleService)
        que incluyó prendas de una o más reservas confirmadas.

        items_reserva_comprados: lista de FittingReservationItem que SÍ
        se acaban de pagar/cobrar en esta venta.

        Marca esas prendas como COMPRADO (su stock ya estaba descontado,
        no se vuelve a tocar). Cualquier OTRA prenda de la MISMA reserva
        que siga PENDIENTE se repone y se quita del otro canal (vía
        liberar_item). La reserva pasa a COMPLETADA.
        """
        from .models import FittingReservation

        reservas_afectadas = set()
        for item in items_reserva_comprados:
            item.estado = "COMPRADO"
            item.save()
            reservas_afectadas.add(item.id_reserva_id)

        for id_reserva in reservas_afectadas:
            reserva = FittingReservation.objects.get(pk=id_reserva)
            for pendiente in list(reserva.items.filter(estado="PENDIENTE")):
                ReservationStockService.liberar_item(
                    pendiente,
                    usuario=usuario,
                    motivo=(
                        f"Reserva #{reserva.id_reserva}: no se compró al "
                        f"completar el resto de la reserva"
                    ),
                )

            reserva.refresh_from_db()
            if reserva.estado not in ("COMPLETADA", "CANCELADA"):
                reserva.estado = "COMPLETADA"
                reserva.save()