"""Pruebas de aislamiento multitenant (RNF02 / 9.6 del enunciado).

Un usuario de la Empresa A no puede consultar, modificar ni eliminar
información de la Empresa B. Se prueba contra la API real (con JWT), no
ocultando opciones en la interfaz.

Ejecutar: python manage.py test apps.users_auth.test_aislamiento
"""
import uuid

from django.test import TestCase

from apps.catalog.models import Sucursal
from apps.sales.models import PosSale
from common.pruebas import (
    cliente_api,
    crear_ciudad,
    crear_empresa,
    crear_plan,
    crear_prenda,
    crear_sucursal,
    crear_usuario,
    filas,
)


class AislamientoEntreEmpresasTests(TestCase):
    """La Empresa A solo ve y modifica lo suyo; lo de la Empresa B responde 404."""

    @classmethod
    def setUpTestData(cls):
        """Dos empresas independientes, cada una con su sucursal, prenda y personal."""
        plan = crear_plan("PRUEBA_PRO", 10)
        ciudad = crear_ciudad()
        cls.empresa_a = crear_empresa("Empresa Prueba A", "empresa-prueba-a", plan)
        cls.empresa_b = crear_empresa("Empresa Prueba B", "empresa-prueba-b", plan)
        cls.sucursal_a = crear_sucursal(cls.empresa_a, "Sucursal A1", ciudad)
        cls.sucursal_b = crear_sucursal(cls.empresa_b, "Sucursal B1", ciudad)
        cls.variante_a = crear_prenda(cls.empresa_a, cls.sucursal_a, "PRUEBA-A-1", 10)
        cls.variante_b = crear_prenda(cls.empresa_b, cls.sucursal_b, "PRUEBA-B-1", 10)
        crear_usuario("admin@prueba-a.test", "ADMIN_EMPRESA", cls.empresa_a)
        crear_usuario("admin@prueba-b.test", "ADMIN_EMPRESA", cls.empresa_b)
        crear_usuario("cajero@prueba-a.test", "CAJERO", cls.empresa_a, cls.sucursal_a)

    def setUp(self):
        """Sesión del administrador de la Empresa A."""
        self.api_a = cliente_api("admin@prueba-a.test")

    def test_lista_de_sucursales_solo_trae_las_propias(self):
        """El listado de sucursales del ADMIN de A no incluye las de B."""
        respuesta = self.api_a.get("/api/catalog/sucursales/")
        ids = {fila["id_sucursal"] for fila in filas(respuesta)}
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(self.sucursal_a.id_sucursal, ids)
        self.assertNotIn(self.sucursal_b.id_sucursal, ids)

    def test_no_puede_ver_sucursal_de_otra_empresa(self):
        """Consultar una sucursal de B responde 404 (no existe para A)."""
        respuesta = self.api_a.get(f"/api/catalog/sucursales/{self.sucursal_b.id_sucursal}/")
        self.assertEqual(respuesta.status_code, 404)

    def test_no_puede_modificar_sucursal_de_otra_empresa(self):
        """Editar una sucursal de B responde 404 y el nombre no cambia."""
        respuesta = self.api_a.patch(
            f"/api/catalog/sucursales/{self.sucursal_b.id_sucursal}/",
            {"nombre": "Cambiada por A"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, 404)
        self.sucursal_b.refresh_from_db()
        self.assertEqual(self.sucursal_b.nombre, "Sucursal B1")

    def test_no_puede_eliminar_sucursal_de_otra_empresa(self):
        """Eliminar una sucursal de B responde 404 y la sucursal sigue existiendo."""
        respuesta = self.api_a.delete(f"/api/catalog/sucursales/{self.sucursal_b.id_sucursal}/")
        self.assertEqual(respuesta.status_code, 404)
        self.assertTrue(Sucursal.objects.filter(pk=self.sucursal_b.pk).exists())

    def test_stock_solo_de_la_propia_empresa(self):
        """El inventario de A no muestra el stock de B."""
        respuesta = self.api_a.get("/api/inventory/stock/", {"page_size": 100})
        sucursales = {fila["id_sucursal"] for fila in filas(respuesta)}
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(sucursales, {self.sucursal_a.id_sucursal})

    def test_no_puede_ver_la_ficha_de_otra_empresa(self):
        """El ADMIN de A no puede abrir la empresa B (404)."""
        respuesta = self.api_a.get(f"/api/auth/empresas/{self.empresa_b.id_empresa}/")
        self.assertEqual(respuesta.status_code, 404)

    def test_bitacora_solo_de_la_propia_empresa(self):
        """La bitácora de A no incluye eventos de la Empresa B (su login, por ejemplo)."""
        from apps.users_auth.models import Bitacora

        cliente_api("admin@prueba-b.test")
        self.assertTrue(Bitacora.objects.filter(id_empresa=self.empresa_b).exists())
        respuesta = self.api_a.get("/api/auth/bitacora/", {"page_size": 100})
        ids = [fila["id_bitacora"] for fila in filas(respuesta)]
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(ids)
        self.assertFalse(Bitacora.objects.filter(pk__in=ids).exclude(id_empresa=self.empresa_a).exists())

    def test_cajero_no_puede_vender_en_sucursal_de_otra_empresa(self):
        """Una venta sin conexión enviada a una sucursal de B se rechaza."""
        api_cajero = cliente_api("cajero@prueba-a.test")
        respuesta = api_cajero.post(
            "/api/sales/sync/ventas-pos/",
            {
                "operaciones": [{
                    "uuid": str(uuid.uuid4()),
                    "id_sucursal": self.sucursal_b.id_sucursal,
                    "metodo_pago": "EFECTIVO",
                    "items": [{"id_variante": self.variante_b.id_variante, "cantidad": 1}],
                }]
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["resultados"][0]["estado"], "RECHAZADA")
        self.assertFalse(PosSale.objects.filter(id_sucursal=self.sucursal_b).exists())