# backend/apps/sales/views.py
from collections import Counter

from django.db import transaction
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from common.permissions import IsCajero, IsCliente, IsEncargadoSucursal, IsRepartidor
from common.tenancy import alcance_de, filtrar_queryset
from common.utils import log_audit
from apps.users_auth.models import Cliente, Empresa, Usuario
from apps.catalog.models import Sucursal
from apps.users_auth.suscripciones import requiere_funcion
from .models import Cart, CartItem, Delivery, Order, OrderItem, PosSale, Devolucion, SyncOperacion
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    OrderSerializer,
    PosSaleSerializer,
    DeliveryEntregaSerializer,
    DevolucionSerializer,
    SyncOperacionSerializer,
)
from .sync import MAX_OPERACIONES_POR_LOTE, SyncService
from .services import CartService, CheckoutService, PosSaleService, DevolucionService
from .integrations.envio import cotizar, EnvioError
from rest_framework.permissions import IsAuthenticated


def _sucursal_activa(sucursal_id):
    """Sucursal ACTIVA de una empresa ACTIVA (el cliente puede comprar en cualquiera)."""
    return Sucursal.objects.select_related("id_empresa").get(
        pk=sucursal_id, estado="ACTIVA", id_empresa__estado="ACTIVA"
    )


class CartViewSet(ReadOnlyModelViewSet):
    """Carritos del cliente. SaaS: tiene un carrito ACTIVO por cada empresa."""

    serializer_class = CartSerializer
    permission_classes = [IsCliente]

    def get_queryset(self):
        """Carritos del cliente autenticado."""
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        return Cart.objects.filter(id_cliente=cliente).select_related("id_empresa")

    @action(detail=False, methods=["get"])
    def actual(self, request):
        """Carrito activo a mostrar.

        Con ?id_empresa=<id> devuelve el de esa empresa. Sin parámetro devuelve
        el último carrito activo usado (compatibilidad con web/móvil actuales).
        """
        cliente = Cliente.objects.get(id_usuario=request.user)
        id_empresa = request.query_params.get("id_empresa")
        if id_empresa:
            empresa = None
            if str(id_empresa).isdigit():
                empresa = Empresa.objects.filter(pk=id_empresa, estado="ACTIVA").first()
            if empresa is None:
                return Response({"error": "Empresa no encontrada."}, status=404)
            return Response(self.get_serializer(CartService.obtener_carrito(cliente, empresa)).data)

        activos = Cart.objects.filter(id_cliente=cliente, estado="ACTIVO").order_by(
            "-fecha_actualizacion"
        )
        # Primero el último carrito con prendas; si no hay, cualquiera activo.
        cart = activos.filter(cartitem__isnull=False).first() or activos.first()
        if cart is None:
            cart = Cart.objects.create(id_cliente=cliente, estado="ACTIVO")
        return Response(self.get_serializer(cart).data)

    @action(detail=False, methods=["get"])
    def activos(self, request):
        """NUEVO (SaaS): todos los carritos activos con prendas, uno por empresa."""
        cliente = Cliente.objects.get(id_usuario=request.user)
        carritos = (
            Cart.objects.filter(id_cliente=cliente, estado="ACTIVO", cartitem__isnull=False)
            .select_related("id_empresa")
            .distinct()
            .order_by("-fecha_actualizacion")
        )
        return Response(self.get_serializer(carritos, many=True).data)

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        """Inicia el pago del carrito de la empresa dueña de la sucursal elegida."""
        cliente = Cliente.objects.get(id_usuario=request.user)
        sucursal_id = request.data.get("id_sucursal")

        if not sucursal_id:
            return Response({"error": "Debe indicar la sucursal de entrega/retiro."}, status=400)
        try:
            sucursal = _sucursal_activa(sucursal_id)
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
        """Confirma el pago de una orden pendiente del cliente."""
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
        """Cotiza el delivery del carrito de la empresa dueña de la sucursal."""
        cliente = Cliente.objects.get(id_usuario=request.user)
        sucursal_id = request.data.get("id_sucursal")
        latitud = request.data.get("latitud")
        longitud = request.data.get("longitud")

        if not sucursal_id or latitud is None or longitud is None:
            return Response({"error": "Debe indicar sucursal, latitud y longitud."}, status=400)
        try:
            sucursal = _sucursal_activa(sucursal_id)
            latitud = float(latitud)
            longitud = float(longitud)
        except Sucursal.DoesNotExist:
            return Response({"error": "Sucursal no encontrada."}, status=400)
        except (TypeError, ValueError):
            return Response({"error": "La ubicación indicada no es válida."}, status=400)
        if not (-90 <= latitud <= 90 and -180 <= longitud <= 180):
            return Response({"error": "La ubicación indicada no es válida."}, status=400)

        cart = CartService.carrito_de_sucursal(cliente, sucursal)
        items = list(cart.cartitem_set.select_related("id_variante")) if cart else []
        if not items:
            return Response(
                {"error": f"No tienes prendas de {sucursal.id_empresa.nombre} en tu carrito."},
                status=400,
            )

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
        """Prendas de todos los carritos activos del cliente."""
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        return CartItem.objects.filter(id_carrito__id_cliente=cliente, id_carrito__estado="ACTIVO")

    def perform_create(self, serializer):
        """Agrega la prenda al carrito de la empresa dueña de esa prenda."""
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        variante = serializer.validated_data["id_variante"]
        empresa = variante.id_producto.id_empresa
        if empresa is None or empresa.estado != "ACTIVA":
            raise ValidationError({"error": "Esta prenda no está disponible."})

        cart = CartService.obtener_carrito(cliente, empresa)
        cantidad_nueva = serializer.validated_data.get("cantidad", 1)
        existente = CartItem.objects.filter(
            id_carrito=cart, id_variante=variante, id_reserva_item__isnull=True
        ).first()
        if existente:
            existente.cantidad += cantidad_nueva
            existente.save()
            serializer.instance = existente
        else:
            serializer.save(id_carrito=cart)
        cart.save(update_fields=["fecha_actualizacion"])

    def perform_destroy(self, instance):
        """Quita la prenda del carrito (si venía de una reserva, repone su stock)."""
        if instance.id_reserva_item_id:
            from apps.reservations.services import ReservationStockService
            ReservationStockService.liberar_item(
                instance.id_reserva_item,
                usuario=self.request.user,
                motivo=(
                    f"Reserva #{instance.id_reserva_item.id_reserva_id}: "
                    f"el cliente quitó la prenda del carrito antes de pagar"
                ),
            )
        instance.delete()


class OrderViewSet(ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsCliente]

    def get_queryset(self):
        """Pedidos del cliente en todas las empresas donde compró."""
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        return (
            Order.objects.filter(id_cliente=cliente)
            .select_related("id_empresa", "id_sucursal")
            .order_by("-fecha_creacion")
        )


class PosSaleViewSet(ReadOnlyModelViewSet):
    serializer_class = PosSaleSerializer
    permission_classes = [IsCajero]

    def get_queryset(self):
        """Ventas presenciales de la empresa del usuario."""
        queryset = PosSale.objects.all().order_by("-fecha_venta")
        return filtrar_queryset(queryset, self.request)

    @action(detail=False, methods=["post"])
    def registrar(self, request):
        """Registra una venta presencial en una sucursal de la empresa del cajero."""
        sucursal_id = request.data.get("id_sucursal")
        metodo_pago = request.data.get("metodo_pago")
        items = request.data.get("items", [])

        if not sucursal_id:
            return Response({"error": "Debe indicar la sucursal."}, status=400)
        if metodo_pago not in ("EFECTIVO", "TARJETA", "QR"):
            return Response({"error": "Método de pago inválido."}, status=400)

        # SaaS: el cajero solo puede vender en sucursales de su empresa.
        try:
            sucursal = filtrar_queryset(Sucursal.objects.all(), request).get(pk=sucursal_id)
        except Sucursal.DoesNotExist:
            return Response({"error": "Sucursal no encontrada."}, status=404)

        try:
            venta = PosSaleService.registrar_venta(request.user, sucursal, items, metodo_pago)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response(PosSaleSerializer(venta).data, status=201)


ROLES_GESTION = ["SUPER_ADMIN", "ADMIN_EMPRESA", "ENCARGADO_SUCURSAL"]


class DeliveryViewSet(ReadOnlyModelViewSet):
    serializer_class = DeliveryEntregaSerializer

    def get_permissions(self):
        """Gestión para encargados; consulta y avance de entregas para repartidores."""
        if self.action in ("preparar", "asignar", "repartidores"):
            return [IsEncargadoSucursal()]
        return [IsRepartidor()]

    def _es_gestor(self):
        """True si el usuario gestiona entregas (no es solo repartidor)."""
        return self.request.user.roles.filter(nombre__in=ROLES_GESTION).exists()

    def get_queryset(self):
        """Entregas de la empresa del usuario (el repartidor solo ve las suyas)."""
        qs = (
            Delivery.objects
            .select_related("id_orden__id_cliente__id_usuario", "id_orden__id_sucursal", "id_repartidor")
            .filter(id_orden__estado__in=["PAGADA", "ENVIADA", "ENTREGADA"])
            .order_by("-fecha_creacion")
        )
        qs = filtrar_queryset(qs, self.request, campo="id_orden__id_empresa")
        if not self._es_gestor():
            qs = qs.filter(id_repartidor=self.request.user)
        estado = self.request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def _repartidores_disponibles(self):
        """Repartidores activos de la empresa del usuario."""
        usuarios = Usuario.objects.filter(estado="ACTIVO", roles__nombre="REPARTIDOR")
        return filtrar_queryset(usuarios, self.request)

    def _auditar(self, request, accion, delivery, texto):
        """Registra en bitácora un cambio de estado de la entrega."""
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
        """Lista los repartidores que se pueden asignar (solo de la propia empresa)."""
        usuarios = self._repartidores_disponibles().order_by("nombres")
        return Response([
            {"id_usuario": u.id_usuario, "nombre": f"{u.nombres} {u.apellidos}"}
            for u in usuarios
        ])

    @action(detail=True, methods=["post"])
    def preparar(self, request, pk=None):
        """Pasa la entrega a EN_PREPARACION."""
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
        """Asigna un repartidor de la misma empresa que el pedido."""
        delivery = self.get_object()
        id_repartidor = request.data.get("id_repartidor")
        if not id_repartidor:
            return Response({"error": "Debe indicar el repartidor."}, status=400)
        try:
            repartidor = self._repartidores_disponibles().filter(
                pk=id_repartidor, id_empresa_id=delivery.id_orden.id_empresa_id
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
        """Marca la entrega EN_CAMINO y la orden como ENVIADA."""
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
        """Marca la entrega ENTREGADO y la orden como ENTREGADA."""
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


# NUEVO (devoluciones)
class DevolucionViewSet(ReadOnlyModelViewSet):
    """
    Devoluciones de pedidos con delivery ya entregados. Solo lectura por
    el router estándar (el cliente ve las suyas, el personal ve las de su
    empresa, filtrable por sucursal - así queda visible en administración);
    la solicitud real pasa por la acción 'solicitar', que valida la orden,
    repone stock y crea Devolucion + DevolucionItem.
    """
    serializer_class = DevolucionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Solicitar es solo para clientes; consultar, para cualquier autenticado."""
        if self.action == "solicitar":
            return [IsCliente()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """El personal ve las devoluciones de su empresa; el cliente, las suyas."""
        queryset = Devolucion.objects.all().order_by("-fecha_creacion")
        alcance = alcance_de(self.request)
        es_personal = self.request.user.roles.filter(
            nombre__in=["SUPER_ADMIN", "ADMIN_EMPRESA", "ENCARGADO_SUCURSAL"]
        ).exists()
        if es_personal:
            queryset = filtrar_queryset(queryset, self.request)
            sucursal = self.request.query_params.get("sucursal")
            if sucursal:
                queryset = queryset.filter(id_orden__id_sucursal_id=sucursal)
            return queryset
        if alcance.es_personal:
            return queryset.none()
        try:
            cliente = Cliente.objects.get(id_usuario=self.request.user)
        except Cliente.DoesNotExist:
            return queryset.none()
        return queryset.filter(id_cliente=cliente)

    @action(detail=False, methods=["post"], permission_classes=[IsCliente])
    def solicitar(self, request):
        """
        Body: {
          "id_orden": <int>,
          "items": [{"id_orden_item": <int>, "cantidad": <int>, "motivo": "TALLA_INCORRECTA"}]
        }
        """
        cliente = Cliente.objects.get(id_usuario=request.user)
        id_orden = request.data.get("id_orden")
        items = request.data.get("items", [])

        if not id_orden:
            return Response({"error": "Debe indicar la orden."}, status=400)
        try:
            orden = Order.objects.get(pk=id_orden, id_cliente=cliente)
        except Order.DoesNotExist:
            return Response({"error": "Orden no encontrada."}, status=400)

        try:
            devolucion, mensajes = DevolucionService.solicitar_devolucion(cliente, orden, items)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response({
            "devolucion": DevolucionSerializer(devolucion).data,
            "mensajes": mensajes,
        }, status=201)


# NUEVO (SaaS - paso 6): sincronización de operaciones hechas sin conexión.
class SyncOperacionViewSet(ReadOnlyModelViewSet):
    """Operaciones sin conexión de la empresa del usuario.

    GET  /api/sales/sync/                 -> historial (?estado=SINCRONIZADA|RECHAZADA)
    POST /api/sales/sync/ventas-pos/      -> sincroniza un lote de ventas POS
        Body: {"operaciones": [{
            "uuid": "<uuid generado en el dispositivo>",
            "fecha_operacion": "2026-10-27T15:30:00-04:00",
            "id_sucursal": <int>,
            "metodo_pago": "EFECTIVO" | "TARJETA" | "QR",
            "items": [{"id_variante": <int>, "cantidad": <int>}]
        }]}
        Respuesta: un resultado por operación con estado SINCRONIZADA,
        DUPLICADA o RECHAZADA (ver apps/sales/sync.py).
    Disponible en los 3 planes (modo offline).
    """

    serializer_class = SyncOperacionSerializer
    permission_classes = [IsCajero, requiere_funcion("modo_offline")]

    def get_queryset(self):
        """Operaciones de la empresa del usuario, de la más reciente a la más antigua."""
        queryset = SyncOperacion.objects.select_related("id_usuario", "id_venta").order_by(
            "-fecha_recepcion"
        )
        queryset = filtrar_queryset(queryset, self.request)
        estado = self.request.query_params.get("estado")
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    @action(detail=False, methods=["post"], url_path="ventas-pos")
    def ventas_pos(self, request):
        """Sincroniza las ventas POS que el dispositivo guardó sin conexión."""
        operaciones = request.data.get("operaciones") if isinstance(request.data, dict) else None
        if not isinstance(operaciones, list) or not operaciones:
            return Response({"error": "Envía la lista de operaciones."}, status=400)
        if len(operaciones) > MAX_OPERACIONES_POR_LOTE:
            return Response(
                {"error": f"Máximo {MAX_OPERACIONES_POR_LOTE} operaciones por envío."},
                status=400,
            )

        sucursales = filtrar_queryset(Sucursal.objects.select_related("id_empresa"), request)
        resultados = SyncService.sincronizar_ventas_pos(request.user, sucursales, operaciones)
        resumen = Counter(resultado["estado"] for resultado in resultados)
        return Response({
            "resultados": resultados,
            "resumen": {
                "SINCRONIZADA": resumen.get("SINCRONIZADA", 0),
                "DUPLICADA": resumen.get("DUPLICADA", 0),
                "RECHAZADA": resumen.get("RECHAZADA", 0),
            },
        })