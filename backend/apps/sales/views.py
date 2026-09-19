from django.db import transaction
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsCajero, IsCliente, IsEncargadoSucursal, IsRepartidor
from common.utils import log_audit
from apps.users_auth.models import Cliente, Usuario
from apps.catalog.models import Sucursal
from .models import Cart, CartItem, Delivery, Order, OrderItem, PosSale
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    OrderSerializer,
    PosSaleSerializer,
    DeliveryEntregaSerializer,
)
from .services import CheckoutService, PosSaleService
from .integrations.envio import cotizar, EnvioError

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

        tipo_entrega = request.data.get("tipo_entrega", "RETIRO")
        entrega = {
            "direccion": request.data.get("direccion"),
            "referencia": request.data.get("referencia"),
            "latitud": request.data.get("latitud"),
            "longitud": request.data.get("longitud"),
        }

        try:
            order, client_secret = CheckoutService.iniciar_checkout(
                cliente, sucursal, tipo_entrega, entrega
            )
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


    @action(detail=False, methods=["post"], url_path="cotizar-envio")
    def cotizar_envio(self, request):
        """
        CU21 - Cotiza el envío a domicilio del carrito actual.
        Body: {"id_sucursal": <int>, "latitud": <float>, "longitud": <float>}
        """
        cliente = Cliente.objects.get(id_usuario=request.user)
        sucursal_id = request.data.get("id_sucursal")
        latitud = request.data.get("latitud")
        longitud = request.data.get("longitud")

        if not sucursal_id or latitud is None or longitud is None:
            return Response({"error": "Debe indicar sucursal, latitud y longitud."}, status=400)
        try:
            sucursal = Sucursal.objects.get(pk=sucursal_id)
            latitud = float(latitud)
            longitud = float(longitud)
        except Sucursal.DoesNotExist:
            return Response({"error": "Sucursal no encontrada."}, status=400)
        except (TypeError, ValueError):
            return Response({"error": "La ubicación indicada no es válida."}, status=400)
        if not (-90 <= latitud <= 90 and -180 <= longitud <= 180):
            return Response({"error": "La ubicación indicada no es válida."}, status=400)

        cart = Cart.objects.filter(id_cliente=cliente, estado="ACTIVO").first()
        items = list(cart.cartitem_set.select_related("id_variante")) if cart else []
        if not items:
            return Response({"error": "El carrito está vacío."}, status=400)

        cantidad_prendas = sum(item.cantidad for item in items)
        subtotal = sum(item.id_variante.precio * item.cantidad for item in items)
        try:
            cotizacion = cotizar(sucursal, latitud, longitud, cantidad_prendas)
        except EnvioError as e:
            return Response({"error": str(e)}, status=400)

        return Response({
            "distancia_km": cotizacion["distancia_km"],
            "costo_envio": cotizacion["costo_envio"],
            "subtotal_productos": subtotal,
            "total": subtotal + cotizacion["costo_envio"],
            "fuente_distancia": cotizacion["fuente_distancia"],
        })

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




ROLES_GESTION = ["SUPER_ADMIN", "ADMIN_EMPRESA", "ENCARGADO_SUCURSAL"]


class DeliveryViewSet(ReadOnlyModelViewSet):
    """
    CU21 - Bandeja de entregas.
    - Encargado/admin: ven todas las entregas de órdenes ya pagadas.
    - Repartidor: solo las que tiene asignadas.
    Filtro opcional: ?estado=PENDIENTE|EN_PREPARACION|EN_CAMINO|ENTREGADO
    """
    serializer_class = DeliveryEntregaSerializer

    def get_permissions(self):
        if self.action in ("preparar", "asignar", "repartidores"):
            return [IsEncargadoSucursal()]
        return [IsRepartidor()]

    def _es_gestor(self):
        return self.request.user.roles.filter(nombre__in=ROLES_GESTION).exists()

    def get_queryset(self):
        qs = (
            Delivery.objects
            .select_related("id_orden__id_cliente__id_usuario", "id_orden__id_sucursal", "id_repartidor")
            .filter(id_orden__estado__in=["PAGADA", "ENVIADA", "ENTREGADA"])
            .order_by("-fecha_creacion")
        )
        if not self._es_gestor():
            qs = qs.filter(id_repartidor=self.request.user)
        estado = self.request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def _auditar(self, request, accion, delivery, texto):
        log_audit(
            usuario=request.user,
            accion=accion,
            tabla_afectada="delivery",
            registro_id=delivery.id_delivery,
            descripcion=(
                f"{request.user.nombres} {request.user.apellidos} {texto} "
                f"(Delivery #{delivery.id_delivery} - Orden #{delivery.id_orden_id})"
            ),
        )

    @action(detail=False, methods=["get"])
    def repartidores(self, request):
        usuarios = Usuario.objects.filter(
            estado="ACTIVO", roles__nombre="REPARTIDOR"
        ).order_by("nombres")
        return Response([
            {"id_usuario": u.id_usuario, "nombre": f"{u.nombres} {u.apellidos}"}
            for u in usuarios
        ])

    @action(detail=True, methods=["post"])
    def preparar(self, request, pk=None):
        delivery = self.get_object()
        with transaction.atomic():
            d = Delivery.objects.select_for_update().get(pk=delivery.pk)
            if d.estado != "PENDIENTE":
                return Response({"error": "Solo se puede preparar una entrega pendiente."}, status=400)
            d.estado = "EN_PREPARACION"
            d.fecha_preparacion = timezone.now()
            d.save()
        self._auditar(request, "ENTREGA_PREPARADA", d, "empezó a preparar el pedido")
        return Response(self.get_serializer(self.get_object()).data)

    @action(detail=True, methods=["post"])
    def asignar(self, request, pk=None):
        delivery = self.get_object()
        id_repartidor = request.data.get("id_repartidor")
        if not id_repartidor:
            return Response({"error": "Debe indicar el repartidor."}, status=400)
        try:
            repartidor = Usuario.objects.filter(
                pk=id_repartidor, estado="ACTIVO", roles__nombre="REPARTIDOR"
            ).first()
        except (TypeError, ValueError):
            repartidor = None
        if not repartidor:
            return Response({"error": "El usuario indicado no es un repartidor activo."}, status=400)
        with transaction.atomic():
            d = Delivery.objects.select_for_update().get(pk=delivery.pk)
            if d.estado not in ("PENDIENTE", "EN_PREPARACION"):
                return Response(
                    {"error": "Solo se puede asignar repartidor antes de que salga el pedido."},
                    status=400,
                )
            d.id_repartidor = repartidor
            d.save()
        self._auditar(request, "ENTREGA_ASIGNADA", d, f"asignó a {repartidor} el pedido")
        return Response(self.get_serializer(self.get_object()).data)

    @action(detail=True, methods=["post"], url_path="en-camino")
    def en_camino(self, request, pk=None):
        delivery = self.get_object()
        with transaction.atomic():
            d = Delivery.objects.select_for_update().get(pk=delivery.pk)
            if d.estado != "EN_PREPARACION":
                return Response({"error": "El pedido debe estar en preparación."}, status=400)
            if d.id_repartidor_id is None:
                return Response({"error": "Primero debe asignarse un repartidor."}, status=400)
            d.estado = "EN_CAMINO"
            d.fecha_en_camino = timezone.now()
            d.save()
            Order.objects.filter(pk=d.id_orden_id).update(estado="ENVIADA")
        self._auditar(request, "ENTREGA_EN_CAMINO", d, "marcó en camino el pedido")
        return Response(self.get_serializer(self.get_object()).data)

    @action(detail=True, methods=["post"])
    def entregar(self, request, pk=None):
        delivery = self.get_object()
        with transaction.atomic():
            d = Delivery.objects.select_for_update().get(pk=delivery.pk)
            if d.estado != "EN_CAMINO":
                return Response({"error": "El pedido debe estar en camino."}, status=400)
            d.estado = "ENTREGADO"
            d.fecha_entrega = timezone.now()
            d.save()
            Order.objects.filter(pk=d.id_orden_id).update(estado="ENTREGADA")
        self._auditar(request, "ENTREGA_COMPLETADA", d, "marcó entregado el pedido")
        return Response(self.get_serializer(self.get_object()).data)