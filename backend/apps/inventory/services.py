from django.db import transaction
from .models import StockItem, InventoryMovement


class StockService:
    @staticmethod
    @transaction.atomic
    def registrar_movimiento(sucursal, variante, usuario, tipo, cantidad, motivo=None):
        stock_item, _ = StockItem.objects.get_or_create(
            id_sucursal=sucursal,
            id_variante=variante,
            defaults={"cantidad": 0},
        )

        if tipo == "ENTRADA":
            stock_item.cantidad += cantidad
        elif tipo == "SALIDA":
            if stock_item.cantidad < cantidad:
                raise ValueError("Stock insuficiente para realizar la salida.")
            stock_item.cantidad -= cantidad
        elif tipo == "AJUSTE":
            stock_item.cantidad = cantidad

        stock_item.save()

        return InventoryMovement.objects.create(
            id_sucursal=sucursal,
            id_variante=variante,
            id_usuario=usuario,
            tipo_movimiento=tipo,
            cantidad=cantidad,
            motivo=motivo,
        )