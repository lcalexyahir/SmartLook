from rest_framework import serializers
from apps.catalog.models import ProductoVariante
from .models import Cart, CartItem, Delivery, Order, OrderItem, PosSale, PosSaleItem


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


# NUEVO (CU21): datos del envío a domicilio de una orden.
class DeliverySerializer(serializers.ModelSerializer):
    repartidor = serializers.SerializerMethodField()

    class Meta:
        model = Delivery
        fields = [
            "id_delivery",
            "direccion",
            "referencia",
            "latitud",
            "longitud",
            "distancia_km",
            "costo_envio",
            "estado",
            "repartidor",
            "fecha_creacion",
            "fecha_preparacion",
            "fecha_en_camino",
            "fecha_entrega",
        ]

    def get_repartidor(self, obj):
        r = obj.id_repartidor
        return f"{r.nombres} {r.apellidos}" if r else None


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source="orderitem_set", many=True, read_only=True)
    sucursal = serializers.StringRelatedField(source="id_sucursal")
    delivery = serializers.SerializerMethodField()

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
            "tipo_entrega",
            "costo_envio",
            "delivery",
            "fecha_creacion",
        ]

    def get_delivery(self, obj):
        delivery = getattr(obj, "delivery", None)
        return DeliverySerializer(delivery).data if delivery else None


# NUEVO (CU16)
class PosSaleItemSerializer(serializers.ModelSerializer):
    variante = serializers.StringRelatedField(source="id_variante", read_only=True)

    class Meta:
        model = PosSaleItem
        fields = ["id_item", "variante", "cantidad", "precio_unitario", "subtotal"]


class PosSaleSerializer(serializers.ModelSerializer):
    sucursal = serializers.StringRelatedField(source="id_sucursal")
    usuario = serializers.StringRelatedField(source="id_usuario")
    items = PosSaleItemSerializer(many=True, read_only=True)

    class Meta:
        model = PosSale
        fields = ["id_venta", "sucursal", "usuario", "items", "total", "metodo_pago", "fecha_venta"]




# NUEVO (CU21): vista de una entrega para la bandeja del personal y el repartidor.
class DeliveryEntregaSerializer(serializers.ModelSerializer):
    orden = serializers.IntegerField(source="id_orden_id", read_only=True)
    cliente = serializers.SerializerMethodField()
    telefono_cliente = serializers.SerializerMethodField()
    sucursal = serializers.StringRelatedField(source="id_orden.id_sucursal")
    total_orden = serializers.DecimalField(
        source="id_orden.total", max_digits=10, decimal_places=2, read_only=True
    )
    estado_orden = serializers.CharField(source="id_orden.estado", read_only=True)
    prendas = serializers.SerializerMethodField()
    repartidor = serializers.SerializerMethodField()

    class Meta:
        model = Delivery
        fields = [
            "id_delivery",
            "orden",
            "cliente",
            "telefono_cliente",
            "sucursal",
            "total_orden",
            "estado_orden",
            "prendas",
            "direccion",
            "referencia",
            "latitud",
            "longitud",
            "distancia_km",
            "costo_envio",
            "estado",
            "id_repartidor",
            "repartidor",
            "fecha_creacion",
            "fecha_preparacion",
            "fecha_en_camino",
            "fecha_entrega",
        ]
        read_only_fields = fields

    def get_cliente(self, obj):
        u = obj.id_orden.id_cliente.id_usuario
        return f"{u.nombres} {u.apellidos}"

    def get_telefono_cliente(self, obj):
        return obj.id_orden.id_cliente.id_usuario.telefono

    def get_prendas(self, obj):
        return sum(item.cantidad for item in obj.id_orden.orderitem_set.all())

    def get_repartidor(self, obj):
        r = obj.id_repartidor
        return f"{r.nombres} {r.apellidos}" if r else None