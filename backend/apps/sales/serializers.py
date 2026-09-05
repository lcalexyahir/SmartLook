from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, PosSale


class CartItemSerializer(serializers.ModelSerializer):
    variante = serializers.StringRelatedField(source="id_variante")

    class Meta:
        model = CartItem
        fields = ["id_item", "variante", "cantidad", "fecha_agregado"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source="cartitem_set", many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id_carrito", "items", "estado", "fecha_actualizacion"]


class OrderItemSerializer(serializers.ModelSerializer):
    variante = serializers.StringRelatedField(source="id_variante")

    class Meta:
        model = OrderItem
        fields = ["id_item", "variante", "cantidad", "precio_unitario", "subtotal"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source="orderitem_set", many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id_orden", "items", "total", "estado", "fecha_creacion"]


class PosSaleSerializer(serializers.ModelSerializer):
    sucursal = serializers.StringRelatedField(source="id_sucursal")
    usuario = serializers.StringRelatedField(source="id_usuario")

    class Meta:
        model = PosSale
        fields = ["id_venta", "sucursal", "usuario", "total", "metodo_pago", "fecha_venta"]