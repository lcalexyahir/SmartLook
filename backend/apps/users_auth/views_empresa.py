"""API de empresas (tenants) y perfil del usuario (SaaS).

Rutas (bajo /api/auth/):
    GET    empresas/                       -> SUPER_ADMIN: todas; ADMIN_EMPRESA: solo la suya
    POST   empresas/                       -> SUPER_ADMIN: registra empresa + administrador + suscripción
    GET    empresas/<id>/                  -> detalle (logo, administrador, plan, vencimiento, sucursales)
    PATCH  empresas/<id>/                  -> SUPER_ADMIN: datos y logo de cualquier empresa;
                                              ADMIN_EMPRESA: logo y contacto de la suya
    POST   empresas/<id>/cambiar-estado/   -> SUPER_ADMIN: {"estado": "ACTIVA" | "SUSPENDIDA"}
    GET    perfil/                         -> datos del usuario autenticado
    PATCH  perfil/                         -> edita nombres, apellidos, teléfono y dirección

El logo se sube como imagen (PNG, JPG o WebP) en base64 ("data:image/...;base64,...").
La web la reduce antes de enviarla; el backend valida el tipo real y el tamaño.

Las empresas no se eliminan (tienen ventas, pedidos y suscripción): se
suspenden. Una empresa suspendida no puede iniciar sesión ni aparece en el
catálogo público. Las sucursales de una empresa se registran con la API de
sucursales (/api/catalog/sucursales/) enviando "id_empresa".
"""
import base64
import binascii
import re

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import mixins, serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from common.permissions import IsAdminEmpresa, IsSuperAdmin
from common.tenancy import alcance_de
from common.utils import get_client_ip, log_audit

from .models import (
    Cliente,
    Empresa,
    PlanSuscripcion,
    Rol,
    Suscripcion,
    Usuario,
    UsuarioRol,
)
from .serializers import TELEFONO_REGEX

ESTADOS_EMPRESA_EDITABLES = ("ACTIVA", "SUSPENDIDA")
CAMPOS_OPCIONALES_EMPRESA = ("nit", "correo_contacto", "telefono", "logo")
# Logo: data URL de una imagen PNG, JPG o WebP (la web la reduce a 256 px antes de enviarla).
PATRON_LOGO = re.compile(r"^data:image/(png|jpeg|webp);base64,(.+)$", re.DOTALL)
FIRMAS_IMAGEN = {
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpeg": (b"\xff\xd8\xff",),
    "webp": (b"RIFF",),
}
MAX_BYTES_LOGO = 1024 * 1024  # 1 MB ya reducida (la web acepta archivos de hasta 10 MB y los achica)


# ---------------------------------------------------------------- utilidades
def normalizar_telefono_persona(valor):
    """RN7: teléfono boliviano de 8 dígitos (6 o 7), con o sin +591. Vacío se permite."""
    if not valor:
        return None
    limpio = valor.strip().replace(" ", "").replace("-", "")
    if limpio.startswith("+591"):
        limpio = limpio[4:]
    elif limpio.startswith("591"):
        limpio = limpio[3:]
    if not TELEFONO_REGEX.match(limpio):
        raise serializers.ValidationError(
            "El teléfono debe tener 8 dígitos y comenzar con 6 o 7 "
            "(formato boliviano), con o sin prefijo +591."
        )
    return limpio


def validar_logo(valor, actual=None):
    """Valida el logo: imagen PNG, JPG o WebP en base64 de hasta 1 MB.

    Vacío = sin logo. Si el valor no cambió respecto al guardado (por ejemplo
    un logo antiguo en formato URL), se acepta tal cual.
    """
    if not valor:
        return None
    valor = valor.strip()
    if actual is not None and valor == actual:
        return valor
    coincidencia = PATRON_LOGO.match(valor)
    if not coincidencia:
        raise serializers.ValidationError("El logo debe ser una imagen PNG, JPG o WebP.")
    tipo = coincidencia.group(1)
    datos = re.sub(r"\s", "", coincidencia.group(2))
    try:
        contenido = base64.b64decode(datos, validate=True)
    except (binascii.Error, ValueError):
        raise serializers.ValidationError("La imagen del logo está dañada.")
    if len(contenido) > MAX_BYTES_LOGO:
        raise serializers.ValidationError("El logo no debe pesar más de 1 MB.")
    # El contenido debe ser realmente del tipo declarado (no solo el encabezado).
    if not contenido.startswith(FIRMAS_IMAGEN[tipo]) or (tipo == "webp" and contenido[8:12] != b"WEBP"):
        raise serializers.ValidationError("El archivo del logo no es una imagen válida.")
    return f"data:image/{tipo};base64,{datos}"


def validar_nombre_empresa(valor, instancia=None):
    """Nombre obligatorio y único (sin distinguir mayúsculas)."""
    valor = (valor or "").strip()
    if not valor:
        raise serializers.ValidationError("El nombre de la empresa es obligatorio.")
    existentes = Empresa.objects.filter(nombre__iexact=valor)
    if instancia is not None:
        existentes = existentes.exclude(pk=instancia.pk)
    if existentes.exists():
        raise serializers.ValidationError("Ya existe una empresa con ese nombre.")
    return valor


def generar_slug(nombre):
    """Slug único a partir del nombre (ej. "LOOK FASHION" -> "look-fashion")."""
    base = slugify(nombre)[:50] or "empresa"
    slug = base
    sufijo = 2
    while Empresa.objects.filter(slug=slug).exists():
        slug = f"{base}-{sufijo}"
        sufijo += 1
    return slug


def vacios_a_nulo(datos, campos):
    """Convierte los textos vacíos en None para no guardar cadenas vacías."""
    for campo in campos:
        if campo in datos and datos[campo] == "":
            datos[campo] = None
    return datos


# ---------------------------------------------------------------- serializers de empresa
class EmpresaSerializer(serializers.ModelSerializer):
    """Empresa con su administrador, su suscripción y el total de sucursales.

    También lo usa el SUPER_ADMIN para editar nombre, NIT, contacto y logo.
    """

    correo_contacto = serializers.EmailField(
        max_length=150, required=False, allow_blank=True, allow_null=True
    )
    administrador = serializers.SerializerMethodField()
    suscripcion = serializers.SerializerMethodField()
    total_sucursales = serializers.SerializerMethodField()

    class Meta:
        model = Empresa
        fields = [
            "id_empresa",
            "uuid",
            "nombre",
            "slug",
            "nit",
            "correo_contacto",
            "telefono",
            "logo",
            "estado",
            "fecha_creacion",
            "administrador",
            "suscripcion",
            "total_sucursales",
        ]
        read_only_fields = ["id_empresa", "uuid", "slug", "estado", "fecha_creacion"]

    def validate_nombre(self, valor):
        """Nombre obligatorio y único."""
        return validar_nombre_empresa(valor, self.instance)

    def validate_logo(self, valor):
        """Imagen del logotipo (PNG, JPG o WebP en base64)."""
        return validar_logo(valor, self.instance.logo if self.instance else None)

    def validate(self, attrs):
        """Guarda los opcionales vacíos como null."""
        return vacios_a_nulo(attrs, CAMPOS_OPCIONALES_EMPRESA)

    def get_administrador(self, obj):
        """Usuario ADMIN_EMPRESA responsable de la empresa."""
        admin = obj.id_administrador
        if admin is None:
            return None
        return {
            "id_usuario": admin.id_usuario,
            "nombre": f"{admin.nombres} {admin.apellidos}",
            "correo": admin.correo,
            "telefono": admin.telefono,
        }

    def get_suscripcion(self, obj):
        """Plan, fechas y días restantes de la suscripción (None si no tiene)."""
        try:
            suscripcion = obj.suscripcion
        except Suscripcion.DoesNotExist:
            return None
        estado = suscripcion.estado
        if estado == "ACTIVA" and not suscripcion.vigente:
            estado = "VENCIDA"
        return {
            "plan_codigo": suscripcion.id_plan.codigo,
            "plan_nombre": suscripcion.id_plan.nombre,
            "fecha_inicio": suscripcion.fecha_inicio,
            "fecha_vencimiento": suscripcion.fecha_vencimiento,
            "estado": estado,
            "vigente": suscripcion.vigente,
            "dias_restantes": suscripcion.dias_restantes,
        }

    def get_total_sucursales(self, obj):
        """Cantidad de sucursales (anotada en la consulta o contada aparte)."""
        total = getattr(obj, "total_sucursales", None)
        if total is None:
            total = obj.sucursales.count()
        return total


class EmpresaContactoSerializer(serializers.ModelSerializer):
    """Lo que el ADMIN_EMPRESA puede editar de su propia empresa."""

    correo_contacto = serializers.EmailField(
        max_length=150, required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = Empresa
        fields = ["correo_contacto", "telefono", "logo"]

    def validate_logo(self, valor):
        """Imagen del logotipo (PNG, JPG o WebP en base64)."""
        return validar_logo(valor, self.instance.logo if self.instance else None)

    def validate(self, attrs):
        """Guarda los opcionales vacíos como null."""
        return vacios_a_nulo(attrs, CAMPOS_OPCIONALES_EMPRESA)


class AdministradorNuevoSerializer(serializers.Serializer):
    """Datos del ADMIN_EMPRESA que se crea junto con la empresa."""

    nombres = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=100)
    correo = serializers.EmailField(max_length=150)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_nombres(self, valor):
        """Nombres sin espacios sobrantes y no vacíos."""
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError("Los nombres son obligatorios.")
        return valor

    def validate_apellidos(self, valor):
        """Apellidos sin espacios sobrantes y no vacíos."""
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError("Los apellidos son obligatorios.")
        return valor

    def validate_correo(self, valor):
        """El correo es el usuario de inicio de sesión: debe ser único."""
        valor = valor.strip()
        if Usuario.objects.filter(correo__iexact=valor).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese correo.")
        return valor

    def validate_telefono(self, valor):
        """RN7: teléfono boliviano."""
        return normalizar_telefono_persona(valor)

    def validate_password(self, valor):
        """RN2: al menos una letra y un número."""
        tiene_letra = any(c.isalpha() for c in valor)
        tiene_numero = any(c.isdigit() for c in valor)
        if not (tiene_letra and tiene_numero):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una letra y un número."
            )
        return valor


class EmpresaCrearSerializer(serializers.Serializer):
    """Registro de una empresa nueva por el SUPER_ADMIN.

    En una sola transacción crea la empresa, su ADMIN_EMPRESA y su
    suscripción. La suscripción queda ACTIVA desde hoy por un periodo del
    plan elegido, sin cobro (contratación simulada administrativamente).
    """

    nombre = serializers.CharField(max_length=150)
    nit = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True)
    correo_contacto = serializers.EmailField(
        max_length=150, required=False, allow_blank=True, allow_null=True
    )
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    logo = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    id_plan = serializers.PrimaryKeyRelatedField(queryset=PlanSuscripcion.objects.filter(estado=True))
    administrador = AdministradorNuevoSerializer()

    def validate_nombre(self, valor):
        """Nombre obligatorio y único."""
        return validar_nombre_empresa(valor)

    def validate_logo(self, valor):
        """Imagen del logotipo (PNG, JPG o WebP en base64)."""
        return validar_logo(valor)

    def validate(self, attrs):
        """Guarda los opcionales vacíos como null."""
        return vacios_a_nulo(attrs, CAMPOS_OPCIONALES_EMPRESA)

    def create(self, validated_data):
        """Crea empresa, administrador (rol ADMIN_EMPRESA) y suscripción de forma atómica."""
        datos_admin = validated_data.pop("administrador")
        plan = validated_data.pop("id_plan")
        rol_admin = Rol.objects.filter(nombre="ADMIN_EMPRESA").first()
        if rol_admin is None:
            raise serializers.ValidationError({"error": "No existe el rol ADMIN_EMPRESA."})
        with transaction.atomic():
            empresa = Empresa.objects.create(
                slug=generar_slug(validated_data["nombre"]),
                estado="ACTIVA",
                **validated_data,
            )
            admin = Usuario.objects.create(
                nombres=datos_admin["nombres"],
                apellidos=datos_admin["apellidos"],
                correo=datos_admin["correo"],
                telefono=datos_admin.get("telefono"),
                password_hash=make_password(datos_admin["password"]),
                estado="ACTIVO",
                id_empresa=empresa,
            )
            UsuarioRol.objects.create(id_usuario=admin, id_rol=rol_admin)
            empresa.id_administrador = admin
            empresa.save(update_fields=["id_administrador"])
            # El vencimiento lo calcula Suscripcion.save() con el periodo del plan.
            Suscripcion.objects.create(
                id_empresa=empresa,
                id_plan=plan,
                fecha_inicio=timezone.localdate(),
                estado="ACTIVA",
            )
        return empresa


# ---------------------------------------------------------------- vista de empresas
class EmpresaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    """Empresas (tenants) de la plataforma.

    - SUPER_ADMIN: lista, registra, edita y suspende/reactiva cualquier empresa.
    - ADMIN_EMPRESA: solo ve su empresa y edita su logo y datos de contacto.
    Lo ajeno responde 404 (no se revela que existe).
    """

    permission_classes = [IsAdminEmpresa]

    def get_permissions(self):
        """Registrar empresas y cambiar su estado: solo SUPER_ADMIN."""
        if self.action in ("create", "cambiar_estado"):
            return [IsSuperAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        """Todas para el SUPER_ADMIN; solo la propia para el ADMIN_EMPRESA."""
        queryset = (
            Empresa.objects.select_related("id_administrador", "suscripcion__id_plan")
            .annotate(total_sucursales=Count("sucursales", distinct=True))
            .order_by("nombre")
        )
        alcance = alcance_de(self.request)
        if alcance.super_admin:
            return queryset
        if alcance.empresa_id is None:
            return queryset.none()
        return queryset.filter(pk=alcance.empresa_id)

    def get_serializer_class(self):
        """Serializer según la acción y el rol."""
        if self.action == "create":
            return EmpresaCrearSerializer
        if self.action in ("update", "partial_update"):
            if alcance_de(self.request).super_admin:
                return EmpresaSerializer
            return EmpresaContactoSerializer
        return EmpresaSerializer

    def _respuesta(self, empresa, codigo=status.HTTP_200_OK):
        """Responde con la empresa completa (administrador, suscripción y sucursales)."""
        empresa = self.get_queryset().get(pk=empresa.pk)
        return Response(EmpresaSerializer(empresa).data, status=codigo)

    def create(self, request, *args, **kwargs):
        """Registra la empresa con su administrador y su suscripción."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        empresa = serializer.save()
        log_audit(
            request.user,
            "EMPRESA_CREADA",
            "empresa",
            empresa.id_empresa,
            f"Se registró la empresa {empresa.nombre} con el plan "
            f"{serializer.validated_data['id_plan'].nombre}",
            direccion_ip=get_client_ip(request),
        )
        return self._respuesta(empresa, status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Edita la empresa según el rol y responde con la empresa completa."""
        parcial = kwargs.pop("partial", False)
        empresa = self.get_object()
        serializer = self.get_serializer(empresa, data=request.data, partial=parcial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_audit(
            request.user,
            "EMPRESA_EDITADA",
            "empresa",
            empresa.id_empresa,
            f"Se editaron los datos de la empresa {empresa.nombre}",
            # El logo se anota como "(imagen)" para no copiar el base64 a la bitácora.
            datos_nuevo={
                campo: ("(imagen)" if campo == "logo" and valor else str(valor))
                for campo, valor in serializer.validated_data.items()
            },
            direccion_ip=get_client_ip(request),
        )
        return self._respuesta(empresa)

    @action(detail=True, methods=["post"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        """Suspende o reactiva una empresa (no se eliminan)."""
        empresa = self.get_object()
        estado = str(request.data.get("estado", "")).strip().upper()
        if estado not in ESTADOS_EMPRESA_EDITABLES:
            return Response(
                {"error": "El estado debe ser ACTIVA o SUSPENDIDA."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        anterior = empresa.estado
        empresa.estado = estado
        empresa.save(update_fields=["estado"])
        log_audit(
            request.user,
            "EMPRESA_ESTADO",
            "empresa",
            empresa.id_empresa,
            f"La empresa {empresa.nombre} pasó de {anterior} a {estado}",
            datos_anterior={"estado": anterior},
            datos_nuevo={"estado": estado},
            direccion_ip=get_client_ip(request),
        )
        return self._respuesta(empresa)


# ---------------------------------------------------------------- perfil del usuario
class PerfilSerializer(serializers.Serializer):
    """Campos que el usuario puede editar de su propio perfil (el correo no)."""

    nombres = serializers.CharField(max_length=100, required=False)
    apellidos = serializers.CharField(max_length=100, required=False)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    direccion = serializers.CharField(max_length=250, required=False, allow_blank=True, allow_null=True)

    def validate_nombres(self, valor):
        """Nombres no vacíos."""
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError("Los nombres son obligatorios.")
        return valor

    def validate_apellidos(self, valor):
        """Apellidos no vacíos."""
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError("Los apellidos son obligatorios.")
        return valor

    def validate_telefono(self, valor):
        """RN7: teléfono boliviano."""
        return normalizar_telefono_persona(valor)

    def validate_direccion(self, valor):
        """Dirección sin espacios sobrantes (vacía = null)."""
        valor = (valor or "").strip()
        return valor or None


def datos_perfil(usuario):
    """Datos del perfil del usuario (los de cliente solo si es cliente)."""
    cliente = Cliente.objects.filter(id_usuario=usuario).first()
    return {
        "id_usuario": usuario.id_usuario,
        "nombres": usuario.nombres,
        "apellidos": usuario.apellidos,
        "correo": usuario.correo,
        "telefono": usuario.telefono,
        "roles": list(usuario.roles.values_list("nombre", flat=True)),
        "empresa_nombre": usuario.id_empresa.nombre if usuario.id_empresa_id else None,
        "sucursal_nombre": usuario.id_sucursal.nombre if usuario.id_sucursal_id else None,
        "es_cliente": cliente is not None,
        "direccion": cliente.direccion if cliente else None,
        "fecha_nacimiento": cliente.fecha_nacimiento if cliente else None,
        "fecha_registro": cliente.fecha_registro if cliente else usuario.fecha_creacion,
    }


class PerfilView(APIView):
    """Perfil del usuario autenticado: consulta (GET) y edición (PATCH)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Devuelve los datos del perfil."""
        return Response(datos_perfil(request.user))

    def patch(self, request):
        """Edita nombres, apellidos, teléfono y (si es cliente) dirección."""
        serializer = PerfilSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        usuario = request.user
        with transaction.atomic():
            campos_usuario = [c for c in ("nombres", "apellidos", "telefono") if c in datos]
            for campo in campos_usuario:
                setattr(usuario, campo, datos[campo])
            if campos_usuario:
                usuario.save(update_fields=campos_usuario)
            if "direccion" in datos:
                Cliente.objects.filter(id_usuario=usuario).update(direccion=datos["direccion"])
        log_audit(
            usuario,
            "PERFIL_ACTUALIZADO",
            "usuarios",
            usuario.id_usuario,
            "El usuario actualizó su perfil",
            datos_nuevo={campo: valor for campo, valor in datos.items()},
            direccion_ip=get_client_ip(request),
        )
        return Response(datos_perfil(usuario))