from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsCajero, IsCliente
from apps.users_auth.models import Cliente
from .models import Cart, CartItem, Order, OrderItem, PosSale
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, PosSaleSerializer


class CartViewSet(ReadOnlyModelViewSet):
    # BUG ENCONTRADO Y CORREGIDO (CU14): antes no tenía permission_classes
    # propio (heredaba IsAuthenticated global) ni get_queryset filtrado -
    # cualquier usuario logueado podía ver el carrito de cualquier cliente.
    serializer_class = CartSerializer
    permission_classes = [IsCliente]

    def get_queryset(self):
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        return Cart.objects.filter(id_cliente=cliente)

    @action(detail=False, methods=["get"])
    def actual(self, request):
        """Devuelve el carrito ACTIVO del cliente logueado, creándolo si no existe."""
        cliente = Cliente.objects.get(id_usuario=request.user)
        cart, _ = Cart.objects.get_or_create(id_cliente=cliente, estado="ACTIVO")
        return Response(self.get_serializer(cart).data)


class CartItemViewSet(ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsCliente]

    def get_queryset(self):
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        return CartItem.objects.filter(id_carrito__id_cliente=cliente, id_carrito__estado="ACTIVO")

    def perform_create(self, serializer):
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        cart, _ = Cart.objects.get_or_create(id_cliente=cliente, estado="ACTIVO")
        variante = serializer.validated_data["id_variante"]
        cantidad_nueva = serializer.validated_data.get("cantidad", 1)
        existente = CartItem.objects.filter(id_carrito=cart, id_variante=variante).first()
        if existente:
            existente.cantidad += cantidad_nueva
            existente.save()
            serializer.instance = existente
        else:
            serializer.save(id_carrito=cart)


class OrderViewSet(ReadOnlyModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class PosSaleViewSet(ModelViewSet):
    queryset = PosSale.objects.all()
    serializer_class = PosSaleSerializer
    permission_classes = [IsCajero]