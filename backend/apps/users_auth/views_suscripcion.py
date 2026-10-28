"""API de planes y suscripciones (SaaS - paso 5).
Rutas (bajo /api/auth/):
    GET    planes/                              -> planes (PLUS, PRO, ULTRA) con precio en USD y Bs
    POST/PUT/PATCH/DELETE planes/...            -> solo SUPER_ADMIN (precios y límites configurables)
    GET    suscripciones/                       -> SUPER_ADMIN: todas; ADMIN_EMPRESA: la suya
    GET    suscripciones/actual/                -> suscripción de mi empresa con su uso
                                                   (todo el personal de la empresa, para
                                                   saber qué funciones incluye su plan)
    GET    suscripciones/pagos/                 -> historial de pagos de suscripción
    POST   suscripciones/iniciar-pago/          -> {"id_plan": <int>} -> client_secret de Stripe
    POST   suscripciones/confirmar-pago/        -> {"referencia_pago": "pi_..."} -> aplica el plan
Los pagos son con Stripe en modo test (sin dinero real). Solo el
ADMIN_EMPRESA paga la suscripción de su propia empresa.
"""
from django.conf import settings
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from common.permissions import IsAdminEmpresa, IsSuperAdmin
from common.tenancy import alcance_de, filtrar_queryset
from common.utils import get_client_ip, log_audit
from .models import PagoSuscripcion, PlanSuscripcion, Suscripcion
from .suscripciones import TIPO_CAMBIO_BOB, SuscripcionService, en_bolivianos
class PlanSuscripcionSerializer(serializers.ModelSerializer):
    precio_bob = serializers.SerializerMethodField()
    tipo_cambio = serializers.SerializerMethodField()
    dias_periodo = serializers.IntegerField(read_only=True)
    class Meta:
        model = PlanSuscripcion
        fields = [
            "id_plan",
            "codigo",
            "nombre",
            "descripcion",
            "precio_usd",
            "precio_bob",
            "tipo_cambio",
            "periodo",
            "dias_periodo",
            "max_sucursales",
            "max_personal",
            "max_productos",
            "delivery",
            "vestidor_virtual",
            "chatbot_clientes",
            "reportes_ia",
            "comparativo_sucursales",
            "modo_offline",
            "estado",
        ]
    def get_precio_bob(self, obj):
        """Precio del periodo en bolivianos."""
        return str(en_bolivianos(obj.precio_usd))
    def get_tipo_cambio(self, obj):
        """Tipo de cambio usado (Bs por dólar)."""
        return str(TIPO_CAMBIO_BOB)
class SuscripcionSerializer(serializers.ModelSerializer):
    empresa = serializers.CharField(source="id_empresa.nombre", read_only=True)
    plan = PlanSuscripcionSerializer(source="id_plan", read_only=True)
    vigente = serializers.BooleanField(read_only=True)
    dias_restantes = serializers.IntegerField(read_only=True)
    uso = serializers.SerializerMethodField()
    class Meta:
        model = Suscripcion
        fields = [
            "id_suscripcion",
            "id_empresa",
            "empresa",
            "plan",
            "fecha_inicio",
            "fecha_vencimiento",
            "estado",
            "vigente",
            "dias_restantes",
            "uso",
        ]
    def get_uso(self, obj):
        """Cuánto usa la empresa de cada límite del plan."""
        from apps.catalog.models import Producto
        empresa = obj.id_empresa
        return {
            "sucursales": empresa.sucursales.count(),
            "personal": empresa.usuarios.count(),
            "productos": Producto.objects.filter(id_empresa=empresa).count(),
        }
class PagoSuscripcionSerializer(serializers.ModelSerializer):
    empresa = serializers.CharField(source="id_empresa.nombre", read_only=True)
    plan = serializers.CharField(source="id_plan.nombre", read_only=True)
    usuario = serializers.StringRelatedField(source="id_usuario", read_only=True)
    class Meta:
        model = PagoSuscripcion
        fields = [
            "id_pago",
            "empresa",
            "plan",
            "usuario",
            "monto_usd",
            "monto_bob",
            "tipo_cambio",
            "referencia_pago",
            "estado",
            "fecha_creacion",
            "fecha_pago",
        ]
class PlanSuscripcionViewSet(ModelViewSet):
    """Planes: cualquier administrador los ve; solo el SUPER_ADMIN los configura."""
    serializer_class = PlanSuscripcionSerializer
    def get_permissions(self):
        """Lectura para administradores; escritura solo para SUPER_ADMIN."""
        if self.action in ("list", "retrieve"):
            return [IsAdminEmpresa()]
        return [IsSuperAdmin()]
    def get_queryset(self):
        """Planes activos ordenados por precio (el SUPER_ADMIN ve también los inactivos)."""
        queryset = PlanSuscripcion.objects.all().order_by("precio_usd", "id_plan")
        if not alcance_de(self.request).super_admin:
            queryset = queryset.filter(estado=True)
        return queryset
class SuscripcionViewSet(ReadOnlyModelViewSet):
    """Suscripciones: cada empresa ve y paga solo la suya; el SUPER_ADMIN ve todas."""
    serializer_class = SuscripcionSerializer
    permission_classes = [IsAdminEmpresa]
    def get_permissions(self):
        """'actual' lo consulta todo el personal (la web oculta lo que el plan no incluye).
        El resto (listar, pagos, pagar) sigue siendo solo de administradores. Quien
        no pertenece a una empresa (SUPER_ADMIN, clientes) recibe 404 en 'actual'.
        """
        if self.action == "actual":
            return [IsAuthenticated()]
        return super().get_permissions()
    def get_queryset(self):
        """Suscripciones dentro del alcance de empresa del usuario."""
        queryset = Suscripcion.objects.select_related("id_empresa", "id_plan").order_by(
            "id_empresa__nombre"
        )
        return filtrar_queryset(queryset, self.request)
    def _empresa_que_paga(self, request):
        """Empresa del ADMIN_EMPRESA que hace el pago (el SUPER_ADMIN no paga)."""
        if alcance_de(request).super_admin or request.user.id_empresa_id is None:
            raise PermissionDenied("Solo el administrador de una empresa paga su suscripción.")
        return request.user.id_empresa
    @action(detail=False, methods=["get"])
    def actual(self, request):
        """Suscripción de la empresa del usuario, con su plan y su uso."""
        if request.user.id_empresa_id is None:
            raise NotFound("Tu usuario no pertenece a ninguna empresa.")
        suscripcion = SuscripcionService.de_empresa(request.user.id_empresa)
        if suscripcion is None:
            raise NotFound("Tu empresa todavía no tiene una suscripción.")
        return Response(self.get_serializer(suscripcion).data)
    @action(detail=False, methods=["get"])
    def pagos(self, request):
        """Historial de pagos de suscripción (de la propia empresa, o todos para SUPER_ADMIN)."""
        pagos = PagoSuscripcion.objects.select_related(
            "id_empresa", "id_plan", "id_usuario"
        ).order_by("-fecha_creacion")
        pagos = filtrar_queryset(pagos, request)
        return Response(PagoSuscripcionSerializer(pagos, many=True).data)
    @action(detail=False, methods=["post"], url_path="iniciar-pago")
    def iniciar_pago(self, request):
        """Inicia el pago (Stripe test) de un periodo del plan elegido."""
        empresa = self._empresa_que_paga(request)
        id_plan = request.data.get("id_plan")
        plan = None
        if str(id_plan).isdigit():
            plan = PlanSuscripcion.objects.filter(pk=id_plan, estado=True).first()
        if plan is None:
            raise ValidationError({"id_plan": "Plan no encontrado."})
        pago, client_secret = SuscripcionService.iniciar_pago(empresa, plan, request.user)
        return Response(
            {
                "pago": PagoSuscripcionSerializer(pago).data,
                "client_secret": client_secret,
                "publishable_key": getattr(settings, "STRIPE_PUBLISHABLE_KEY", ""),
            },
            status=status.HTTP_201_CREATED,
        )
    @action(detail=False, methods=["post"], url_path="confirmar-pago")
    def confirmar_pago(self, request):
        """Confirma el pago con Stripe y activa o renueva el plan pagado."""
        empresa = self._empresa_que_paga(request)
        referencia = request.data.get("referencia_pago")
        if not referencia:
            raise ValidationError({"referencia_pago": "Falta la referencia de pago."})
        suscripcion, pago = SuscripcionService.confirmar_pago(empresa, referencia)
        log_audit(
            request.user,
            "SUSCRIPCION_PAGADA",
            "suscripcion",
            suscripcion.id_suscripcion,
            (
                f"{empresa.nombre} pagó el plan {pago.id_plan.nombre}: "
                f"USD {pago.monto_usd} (Bs {pago.monto_bob}). "
                f"Vence el {suscripcion.fecha_vencimiento:%d/%m/%Y}."
            ),
            datos_nuevo={"referencia_pago": pago.referencia_pago, "plan": pago.id_plan.codigo},
            direccion_ip=get_client_ip(request),
        )
        return Response(self.get_serializer(suscripcion).data)