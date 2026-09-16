from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsCajero, IsCliente
from apps.users_auth.models import Cliente
from apps.catalog.models import Sucursal
from .models import Cart, CartItem, Order, OrderItem, PosSale
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, PosSaleSerializer
from .services import CheckoutService, PosSaleService

class CartViewSet(ReadOnlyModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsCliente]

    def get_queryset(self):
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        return Cart.objects.filter(id_cliente=cliente)

    @action(detail=False, methods=["get"])
    def actual(self, request):
        cliente = Cliente.objects.get(id_usuario=request.user)
        cart, _ = Cart.objects.get_or_create(id_cliente=cliente, estado="ACTIVO")
        return Response(self.get_serializer(cart).data)

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        cliente = Cliente.objects.get(id_usuario=request.user)
        sucursal_id = request.data.get("id_sucursal")

        if not sucursal_id:
            return Response({"error": "Debe indicar la sucursal de entrega/retiro."}, status=400)
        try:
            sucursal = Sucursal.objects.get(pk=sucursal_id)
        except Sucursal.DoesNotExist:
            return Response({"error": "Sucursal no encontrada."}, status=400)

        try:
            order, client_secret = CheckoutService.iniciar_checkout(cliente, sucursal)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response({
            "orden": OrderSerializer(order).data,
            "client_secret": client_secret,
        }, status=201)

    @action(detail=False, methods=["post"])
    def confirmar_pago(self, request):
        cliente = Cliente.objects.get(id_usuario=request.user)
        referencia_pago = request.data.get("referencia_pago")

        if not referencia_pago:
            return Response({"error": "Falta la referencia de pago."}, status=400)

        try:
            order = CheckoutService.confirmar_pago(cliente, referencia_pago)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response(OrderSerializer(order).data, status=200)

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
    serializer_class = OrderSerializer
    permission_classes = [IsCliente]

    def get_queryset(self):
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        return Order.objects.filter(id_cliente=cliente).order_by("-fecha_creacion")

class PosSaleViewSet(ReadOnlyModelViewSet):
    """
    CU16 - Solo lectura por el router estándar; el registro real de la
    venta pasa por la acción 'registrar' (necesita validar stock y
    crear los items, no un simple create() de DRF).
    """
    queryset = PosSale.objects.all().order_by("-fecha_venta")
    serializer_class = PosSaleSerializer
    permission_classes = [IsCajero]

    @action(detail=False, methods=["post"])
    def registrar(self, request):
        """
        Body: {
          "id_sucursal": <int>,
          "metodo_pago": "EFECTIVO" | "TARJETA" | "QR",
          "items": [{"id_variante": <int>, "cantidad": <int>}, ...]
        }
        """
        sucursal_id = request.data.get("id_sucursal")
        metodo_pago = request.data.get("metodo_pago")
        items = request.data.get("items", [])

        if not sucursal_id:
            return Response({"error": "Debe indicar la sucursal."}, status=400)
        if metodo_pago not in ("EFECTIVO", "TARJETA", "QR"):
            return Response({"error": "Método de pago inválido."}, status=400)

        try:
            sucursal = Sucursal.objects.get(pk=sucursal_id)
        except Sucursal.DoesNotExist:
            return Response({"error": "Sucursal no encontrada."}, status=400)

        try:
            venta = PosSaleService.registrar_venta(request.user, sucursal, items, metodo_pago)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response(PosSaleSerializer(venta).data, status=201)