"""Aislamiento multitenant (SaaS) de SmartLook.

La empresa es el tenant. Todas las vistas usan estas utilidades para
decidir qué registros puede ver o modificar el usuario autenticado. La
regla se aplica SIEMPRE en el backend, nunca solo ocultando opciones en
la interfaz.

Alcance según quién hace la petición:
    SUPER_ADMIN       -> todas las empresas (opcional ?empresa=<slug>).
    Personal empresa  -> solo su empresa (ADMIN_EMPRESA, ENCARGADO_SUCURSAL,
                         CAJERO, REPARTIDOR). Lo ajeno responde 404.
    Cliente/visitante -> en vistas públicas (catálogo) ve todas las empresas
                         activas y con suscripción vigente (catálogo unificado,
                         opcional ?empresa=<slug>); en vistas privadas no ve nada.
"""
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import SAFE_METHODS

ROLES_PERSONAL = ("ADMIN_EMPRESA", "ENCARGADO_SUCURSAL", "CAJERO", "REPARTIDOR")


class Alcance:
    """Resume, una sola vez por petición, a qué empresas tiene acceso el usuario."""

    def __init__(self, request):
        """Calcula el alcance a partir del usuario y de ?empresa=<slug>."""
        usuario = request.user
        self.autenticado = bool(getattr(usuario, "is_authenticated", False))
        nombres_roles = set()
        if self.autenticado:
            nombres_roles = set(usuario.roles.values_list("nombre", flat=True))
        self.super_admin = "SUPER_ADMIN" in nombres_roles
        self.es_personal = not self.super_admin and bool(nombres_roles & set(ROLES_PERSONAL))
        self.empresa_id = usuario.id_empresa_id if self.es_personal else None
        params = getattr(request, "query_params", request.GET)
        self.slug_filtro = (params.get("empresa") or "").strip() or None


def alcance_de(request):
    """Devuelve el Alcance de la petición, calculándolo solo la primera vez."""
    alcance = getattr(request, "_alcance_tenant", None)
    if alcance is None:
        alcance = Alcance(request)
        request._alcance_tenant = alcance
    return alcance


def filtrar_queryset(queryset, request, campo="id_empresa", publico=False):
    """Restringe un queryset a las empresas que el usuario puede ver.

    campo:   ruta hasta la empresa (ej. "id_empresa" o "id_producto__id_empresa").
    publico: True si clientes y visitantes pueden leerlo (catálogo unificado).
    """
    alcance = alcance_de(request)
    if alcance.super_admin:
        if alcance.slug_filtro:
            return queryset.filter(**{f"{campo}__slug": alcance.slug_filtro})
        return queryset
    if alcance.es_personal:
        if alcance.empresa_id is None:
            return queryset.none()
        return queryset.filter(**{campo: alcance.empresa_id})
    if publico:
        # Paso 5: una empresa con la suscripción vencida desaparece del catálogo.
        queryset = queryset.filter(**{
            f"{campo}__estado": "ACTIVA",
            f"{campo}__suscripcion__estado": "ACTIVA",
            f"{campo}__suscripcion__fecha_vencimiento__gte": timezone.localdate(),
        })
        if alcance.slug_filtro:
            queryset = queryset.filter(**{f"{campo}__slug": alcance.slug_filtro})
        return queryset
    return queryset.none()


def empresa_para_crear(request):
    """Devuelve la Empresa a la que se asignará un registro nuevo.

    El personal siempre crea en su propia empresa (no puede elegir otra).
    El SUPER_ADMIN debe indicarla con "id_empresa" en el cuerpo o con
    ?empresa=<slug>.
    """
    from apps.users_auth.models import Empresa

    alcance = alcance_de(request)
    if alcance.es_personal:
        if alcance.empresa_id is None:
            raise PermissionDenied("Tu usuario no está asociado a ninguna empresa.")
        return Empresa.objects.get(pk=alcance.empresa_id)
    if alcance.super_admin:
        id_empresa = request.data.get("id_empresa") if hasattr(request, "data") else None
        empresa = None
        if id_empresa:
            empresa = Empresa.objects.filter(pk=id_empresa).first()
        elif alcance.slug_filtro:
            empresa = Empresa.objects.filter(slug=alcance.slug_filtro).first()
        if empresa is None:
            raise ValidationError({"id_empresa": "Indica a qué empresa pertenece el registro."})
        return empresa
    raise PermissionDenied("No tienes permiso para crear registros de una empresa.")


def empresa_id_de_objeto(objeto):
    """Devuelve el id de empresa de un registro (directo o a través de su padre).

    Devuelve None si el registro es global (Talla, Color, Ciudad...).
    """
    if objeto is None:
        return None
    if hasattr(objeto, "id_empresa_id"):
        return objeto.id_empresa_id
    for padre in ("id_producto", "id_sucursal", "id_orden", "id_reserva", "id_venta", "id_carrito"):
        if hasattr(objeto, f"{padre}_id"):
            return empresa_id_de_objeto(getattr(objeto, padre))
    return None


def validar_relaciones(datos, empresa_id):
    """Rechaza datos que apunten a registros de otra empresa.

    Recorre los valores validados por el serializer: cualquier registro
    relacionado (categoría, producto, sucursal...) debe pertenecer a la
    misma empresa. Los registros globales (talla, color, ciudad) se aceptan.
    """
    for campo, valor in datos.items():
        if not hasattr(valor, "_meta"):
            continue
        id_relacion = empresa_id_de_objeto(valor)
        if id_relacion is not None and id_relacion != empresa_id:
            raise ValidationError({campo: "El registro indicado pertenece a otra empresa."})


class EmpresaScopedMixin:
    """Mixin para ViewSets de registros que pertenecen a una empresa.

    - get_queryset: llamar a self.filtrar_por_empresa(queryset) al final.
    - Crear: asigna la empresa del usuario (no se acepta otra desde el cliente).
    - Crear/editar: verifica que los registros relacionados sean de la misma empresa.
    Los registros de otra empresa no aparecen en el queryset, así que
    consultarlos, editarlos o borrarlos responde 404.
    """

    campo_empresa = "id_empresa"
    lectura_publica = False
    asigna_empresa = True

    def filtrar_por_empresa(self, queryset):
        """Aplica el alcance de empresa del usuario al queryset."""
        publico = self.lectura_publica and self.request.method in SAFE_METHODS
        return filtrar_queryset(queryset, self.request, self.campo_empresa, publico)

    def es_vista_publica(self):
        """True si quien consulta es cliente o visitante (catálogo unificado)."""
        alcance = alcance_de(self.request)
        return not (alcance.super_admin or alcance.es_personal)

    def perform_create(self, serializer):
        """Crea el registro dentro de la empresa del usuario."""
        if self.asigna_empresa:
            empresa = empresa_para_crear(self.request)
            validar_relaciones(serializer.validated_data, empresa.id_empresa)
            serializer.save(id_empresa=empresa)
            return
        alcance = alcance_de(self.request)
        if alcance.es_personal:
            validar_relaciones(serializer.validated_data, alcance.empresa_id)
        serializer.save()

    def perform_update(self, serializer):
        """Edita el registro sin permitir enlazarlo a datos de otra empresa."""
        empresa_id = empresa_id_de_objeto(serializer.instance)
        if empresa_id is not None:
            validar_relaciones(serializer.validated_data, empresa_id)
        serializer.save()