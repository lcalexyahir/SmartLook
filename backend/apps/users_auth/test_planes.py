"""Pruebas de los límites y la vigencia del plan de suscripción (9.4 / 9.5).

- Un plan con límite de 2 sucursales no deja registrar la tercera (403,
  codigo "plan_no_permitido") y no la guarda.
- Al cambiar a un plan con más sucursales se puede volver a registrar.
- Con la suscripción vencida solo se puede consultar (402,
  codigo "suscripcion_vencida" al intentar registrar).

Ejecutar: python manage.py test apps.users_auth.test_planes
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Sucursal
from apps.users_auth.models import Suscripcion
from common.pruebas import (
    cliente_api,
    crear_ciudad,
    crear_empresa,
    crear_plan,
    crear_sucursal,
    crear_usuario,
)


class LimiteDeSucursalesTests(TestCase):
    """El plan limita cuántas sucursales puede tener la empresa."""

    @classmethod
    def setUpTestData(cls):
        """Empresa con plan de 2 sucursales que ya tiene 1."""
        cls.plan_basico = crear_plan("PRUEBA_BASICO", 2)
        cls.plan_amplio = crear_plan("PRUEBA_AMPLIO", 10)
        cls.ciudad = crear_ciudad()
        cls.empresa = crear_empresa("Empresa Plan Prueba", "empresa-plan-prueba", cls.plan_basico)
        crear_sucursal(cls.empresa, "Sucursal Uno", cls.ciudad)
        crear_usuario("admin@plan-prueba.test", "ADMIN_EMPRESA", cls.empresa)

    def setUp(self):
        """Sesión del administrador de la empresa."""
        self.api = cliente_api("admin@plan-prueba.test")

    def registrar_sucursal(self, nombre):
        """POST de una sucursal nueva por la API."""
        return self.api.post(
            "/api/catalog/sucursales/",
            {"nombre": nombre, "direccion": "Direccion de prueba", "id_ciudad": self.ciudad.id_ciudad},
            format="json",
        )

    def total_sucursales(self):
        """Sucursales que tiene la empresa en la base de datos."""
        return Sucursal.objects.filter(id_empresa=self.empresa).count()

    def test_permite_hasta_el_limite_del_plan(self):
        """Con 1 de 2 sucursales, la segunda se registra (201)."""
        respuesta = self.registrar_sucursal("Sucursal Dos")
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(self.total_sucursales(), 2)

    def test_bloquea_al_superar_el_limite(self):
        """Con 2 de 2 sucursales, la tercera se rechaza (403) y no se guarda."""
        self.assertEqual(self.registrar_sucursal("Sucursal Dos").status_code, 201)
        respuesta = self.registrar_sucursal("Sucursal Tres")
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(respuesta.data["codigo"], "plan_no_permitido")
        self.assertEqual(self.total_sucursales(), 2)

    def test_cambiar_a_plan_superior_permite_registrar(self):
        """Tras pasar a un plan de 10 sucursales, la tercera ya se registra."""
        self.registrar_sucursal("Sucursal Dos")
        Suscripcion.objects.filter(id_empresa=self.empresa).update(id_plan=self.plan_amplio)
        respuesta = self.registrar_sucursal("Sucursal Tres")
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(self.total_sucursales(), 3)

    def test_suscripcion_vencida_solo_permite_consultar(self):
        """Con la suscripción vencida: registrar responde 402, consultar sigue funcionando."""
        ayer = timezone.localdate() - timedelta(days=1)
        Suscripcion.objects.filter(id_empresa=self.empresa).update(fecha_vencimiento=ayer)
        respuesta = self.registrar_sucursal("Sucursal Dos")
        self.assertEqual(respuesta.status_code, 402)
        self.assertEqual(respuesta.data["codigo"], "suscripcion_vencida")
        self.assertEqual(self.total_sucursales(), 1)
        self.assertEqual(self.api.get("/api/catalog/sucursales/").status_code, 200)