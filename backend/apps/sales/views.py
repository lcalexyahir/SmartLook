from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from common.permissions import IsCajero
from .models import Cart, CartItem, Order, OrderItem, PosSale
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, PosSaleSerializer


class CartViewSet(ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer


class OrderViewSet(ReadOnlyModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class PosSaleViewSet(ModelViewSet):
    queryset = PosSale.objects.all()
    serializer_class = PosSaleSerializer
    permission_classes = [IsCajero]