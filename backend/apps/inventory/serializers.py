from rest_framework import serializers
from .models import StockItem, InventoryMovement


class StockItemSerializer(serializers.ModelSerializer):
    sucursal = serializers.StringRelatedField(source="id_sucursal")
    variante = serializers.StringRelatedField(source="id_variante")
    # Campos añadidos para CU08 (disponibilidad por sucursal, vista cliente)
    id_sucursal = serializers.IntegerField(source="id_sucursal.id_sucursal", read_only=True)
    sucursal_nombre = serializers.CharField(source="id_sucursal.nombre", read_only=True)
    ciudad = serializers.CharField(source="id_sucursal.id_ciudad.nombre", read_only=True)
    direccion = serializers.CharField(source="id_sucursal.direccion", read_only=True)
    disponible = serializers.SerializerMethodField()

    class Meta:
        model = StockItem
        fields = [
            "id_stock",
            "sucursal",
            "variante",
            "id_sucursal",
            "sucursal_nombre",
            "ciudad",
            "direccion",
            "cantidad",
            "disponible",
            "stock_minimo",
            "stock_maximo",
            "estado",
            "fecha_actualizacion",
        ]

    def get_disponible(self, obj):
        return obj.cantidad > 0


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