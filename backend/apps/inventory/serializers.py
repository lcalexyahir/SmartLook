from rest_framework import serializers
from .models import StockItem, InventoryMovement


class StockItemSerializer(serializers.ModelSerializer):
    sucursal = serializers.StringRelatedField(source="id_sucursal")
    variante = serializers.StringRelatedField(source="id_variante")

    class Meta:
        model = StockItem
        fields = [
            "id_stock",
            "sucursal",
            "variante",
            "cantidad",
            "stock_minimo",
            "stock_maximo",
            "estado",
            "fecha_actualizacion",
        ]


class InventoryMovementSerializer(serializers.ModelSerializer):
    sucursal = serializers.StringRelatedField(source="id_sucursal")
    variante = serializers.StringRelatedField(source="id_variante")
    usuario = serializers.StringRelatedField(source="id_usuario")

    class Meta:
        model = InventoryMovement
        fields = [
            "id_movimiento",
            "sucursal",
            "variante",
            "usuario",
            "tipo_movimiento",
            "cantidad",
            "motivo",
            "fecha_movimiento",
        ]