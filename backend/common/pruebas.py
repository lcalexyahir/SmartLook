"""Datos para las pruebas automáticas del SaaS (B).

Cada prueba crea sus propias empresas, planes, usuarios, sucursales y prendas
en la base de datos de pruebas que Django crea y borra sola
(test_<nombre de la base>); nunca usa ni modifica los datos reales.
Los usuarios inician sesión por POST /api/auth/login/, así que las pruebas
pasan por la autenticación JWT real (SmartLookJWTAuthentication).
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import (
    Categoria,
    Ciudad,
    Color,
    Pais,
    Producto,
    ProductoVariante,
    Sucursal,
    Talla,
)
from apps.inventory.models import StockItem
from apps.users_auth.models import (
    Cliente,
    Empresa,
    PlanSuscripcion,
    Rol,
    Suscripcion,
    Usuario,
    UsuarioRol,
)

CLAVE = "Prueba12345"


def crear_plan(codigo, max_sucursales):
    """Plan de prueba con el límite de sucursales indicado (None = ilimitado)."""
    plan, _ = PlanSuscripcion.objects.get_or_create(
        codigo=codigo,
        defaults={
            "nombre": f"Plan {codigo}",
            "precio_usd": Decimal("20.00"),
            "periodo": "MENSUAL",
            "max_sucursales": max_sucursales,
            "modo_offline": True,
            "comparativo_sucursales": True,
        },
    )
    return plan


def crear_empresa(nombre, slug, plan, dias_vigencia=30):
    """Empresa activa con su suscripción al plan indicado."""
    empresa = Empresa.objects.create(nombre=nombre, slug=slug, estado="ACTIVA")
    hoy = timezone.localdate()
    Suscripcion.objects.create(
        id_empresa=empresa,
        id_plan=plan,
        fecha_inicio=hoy,
        fecha_vencimiento=hoy + timedelta(days=dias_vigencia),
        estado="ACTIVA",
    )
    return empresa


def crear_ciudad():
    """Ciudad de prueba (las ciudades son globales)."""
    pais, _ = Pais.objects.get_or_create(nombre="Pais de prueba")
    ciudad, _ = Ciudad.objects.get_or_create(id_pais=pais, nombre="Ciudad de prueba")
    return ciudad


def crear_sucursal(empresa, nombre, ciudad):
    """Sucursal activa de la empresa."""
    return Sucursal.objects.create(
        id_empresa=empresa,
        id_ciudad=ciudad,
        nombre=nombre,
        direccion="Direccion de prueba",
        estado="ACTIVA",
    )


def crear_usuario(correo, rol, empresa=None, sucursal=None):
    """Usuario con un rol; si es CLIENTE también se crea su ficha de cliente."""
    usuario = Usuario.objects.create(
        nombres="Usuario",
        apellidos="Prueba",
        correo=correo,
        password_hash=make_password(CLAVE),
        estado="ACTIVO",
        id_empresa=empresa,
        id_sucursal=sucursal,
    )
    rol_obj, _ = Rol.objects.get_or_create(nombre=rol)
    UsuarioRol.objects.create(id_usuario=usuario, id_rol=rol_obj)
    if rol == "CLIENTE":
        Cliente.objects.create(id_usuario=usuario)
    return usuario


def crear_prenda(empresa, sucursal, codigo, stock):
    """Producto con una variante y su stock en la sucursal indicada."""
    categoria, _ = Categoria.objects.get_or_create(nombre="Poleras", id_empresa=empresa)
    producto = Producto.objects.create(
        id_categoria=categoria,
        id_empresa=empresa,
        nombre=f"Polera {codigo}",
        tipo_prenda="Polera",
    )
    talla, _ = Talla.objects.get_or_create(nombre="M")
    color, _ = Color.objects.get_or_create(nombre="Negro", defaults={"codigo_hex": "#000000"})
    variante = ProductoVariante.objects.create(
        id_producto=producto,
        id_talla=talla,
        id_color=color,
        codigo_producto=codigo,
        precio=Decimal("100.00"),
        cantidad=stock,
    )
    StockItem.objects.create(
        id_sucursal=sucursal,
        id_variante=variante,
        cantidad=stock,
        id_empresa=empresa,
    )
    return variante


def cliente_api(correo):
    """APIClient con el token JWT obtenido iniciando sesión de verdad."""
    api = APIClient()
    respuesta = api.post("/api/auth/login/", {"correo": correo, "password": CLAVE}, format="json")
    assert respuesta.status_code == 200, respuesta.data
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {respuesta.data['tokens']['access']}")
    return api


def filas(respuesta):
    """Filas de una respuesta, esté paginada o no."""
    datos = respuesta.data
    return datos.get("results", datos) if isinstance(datos, dict) else datos