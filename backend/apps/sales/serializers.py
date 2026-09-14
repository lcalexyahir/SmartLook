from rest_framework import serializers
from apps.catalog.models import ProductoVariante
from .models import Cart, CartItem, Order, OrderItem, PosSale

class CartItemSerializer(serializers.ModelSerializer):
    variante = serializers.StringRelatedField(source="id_variante", read_only=True)
    id_variante = serializers.PrimaryKeyRelatedField(
        queryset=ProductoVariante.objects.all(), write_only=True
    )
    precio_unitario = serializers.DecimalField(
        source="id_variante.precio", max_digits=10, decimal_places=2, read_only=True
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id_item",
            "variante",
            "id_variante",
            "cantidad",
            "precio_unitario",
            "subtotal",
            "fecha_agregado",
        ]

    def get_subtotal(self, obj):
        return obj.id_variante.precio * obj.cantidad

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source="cartitem_set", many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id_carrito", "items", "estado", "total", "fecha_actualizacion"]

    def get_total(self, obj):
        return sum(item.id_variante.precio * item.cantidad for item in obj.cartitem_set.all())

class OrderItemSerializer(serializers.ModelSerializer):
    variante = serializers.StringRelatedField(source="id_variante")

    class Meta:
        model = OrderItem
        fields = ["id_item", "variante", "cantidad", "precio_unitario", "subtotal"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source="orderitem_set", many=True, read_only=True)
    # NUEVO (CU15): sucursal, método y referencia de pago visibles en la orden.
    sucursal = serializers.StringRelatedField(source="id_sucursal")

    class Meta:
        model = Order
        fields = [
            "id_orden",
            "items",
            "total",
            "estado",
            "metodo_pago",
            "referencia_pago",
            "sucursal",
            "fecha_creacion",
        ]

class PosSaleSerializer(serializers.ModelSerializer):
    sucursal = serializers.StringRelatedField(source="id_sucursal")
    usuario = serializers.StringRelatedField(source="id_usuario")

    class Meta:
        model = PosSale
        fields = ["id_venta", "sucursal", "usuario", "total", "metodo_pago", "fecha_venta"]