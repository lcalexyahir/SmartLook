"""Pruebas de la sincronización sin conexión (5.4, RNF05 idempotencia, RNF06).

- Una venta POS hecha sin conexión se registra una sola vez aunque el
  dispositivo la reenvíe (mismo UUID = DUPLICADA, sin descontar stock dos veces).
- Si no hay stock al sincronizar, se rechaza con el motivo y queda en el
  historial; reenviarla no la registra.
- Lo mismo para las reservas de prendas hechas sin conexión por el cliente.

Ejecutar: python manage.py test apps.sales.test_sincronizacion
"""
import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.inventory.models import StockItem
from apps.reservations.models import FittingReservation
from apps.sales.models import PosSale, SyncOperacion
from common.pruebas import (
    cliente_api,
    crear_ciudad,
    crear_empresa,
    crear_plan,
    crear_prenda,
    crear_sucursal,
    crear_usuario,
)

URL_VENTAS = "/api/sales/sync/ventas-pos/"
URL_RESERVAS = "/api/reservations/reservas/sync/"


class SincronizacionTests(TestCase):
    """Idempotencia y rechazos de las operaciones sin conexión."""

    @classmethod
    def setUpTestData(cls):
        """Empresa con una sucursal, una prenda con 5 unidades, un cajero y un cliente."""
        plan = crear_plan("PRUEBA_SYNC", 10)
        cls.empresa = crear_empresa("Empresa Sync Prueba", "empresa-sync-prueba", plan)
        cls.sucursal = crear_sucursal(cls.empresa, "Sucursal Sync", crear_ciudad())
        cls.variante = crear_prenda(cls.empresa, cls.sucursal, "PRUEBA-SYNC-1", 5)
        crear_usuario("cajero@sync-prueba.test", "CAJERO", cls.empresa, cls.sucursal)
        crear_usuario("cliente@sync-prueba.test", "CLIENTE")

    def setUp(self):
        """Sesiones del cajero y del cliente."""
        self.cajero = cliente_api("cajero@sync-prueba.test")
        self.cliente = cliente_api("cliente@sync-prueba.test")

    # ---------------------------------------------------------------- utilidades
    def venta(self, cantidad=1, id_uuid=None):
        """Operación de venta POS como la arma la web o el móvil."""
        return {
            "uuid": id_uuid or str(uuid.uuid4()),
            "fecha_operacion": timezone.now().isoformat(),
            "id_sucursal": self.sucursal.id_sucursal,
            "metodo_pago": "EFECTIVO",
            "items": [{"id_variante": self.variante.id_variante, "cantidad": cantidad}],
        }

    def reserva(self, id_uuid=None):
        """Operación de reserva como la arma la web o el móvil."""
        manana = (timezone.localdate() + timedelta(days=1)).isoformat()
        return {
            "uuid": id_uuid or str(uuid.uuid4()),
            "fecha_operacion": timezone.now().isoformat(),
            "id_sucursal": self.sucursal.id_sucursal,
            "fecha_reserva": manana,
            "hora_reserva": "16:00",
            "items": [{"id_variante": self.variante.id_variante}],
        }

    def enviar(self, api, url, operaciones):
        """Envía un lote y devuelve los resultados."""
        respuesta = api.post(url, {"operaciones": operaciones}, format="json")
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        return respuesta.data["resultados"]

    def stock(self):
        """Unidades de la prenda en la sucursal."""
        return StockItem.objects.get(id_sucursal=self.sucursal, id_variante=self.variante).cantidad

    # ---------------------------------------------------------------- ventas POS
    def test_venta_se_registra_y_descuenta_stock(self):
        """La primera vez la venta queda SINCRONIZADA y descuenta el stock."""
        resultado = self.enviar(self.cajero, URL_VENTAS, [self.venta(cantidad=2)])[0]
        self.assertEqual(resultado["estado"], "SINCRONIZADA")
        self.assertIsNotNone(resultado["id_venta"])
        self.assertEqual(self.stock(), 3)

    def test_reenviar_la_misma_venta_no_la_duplica(self):
        """El mismo UUID enviado otra vez responde DUPLICADA con la venta original."""
        operacion = self.venta()
        primera = self.enviar(self.cajero, URL_VENTAS, [operacion])[0]
        segunda = self.enviar(self.cajero, URL_VENTAS, [operacion])[0]
        self.assertEqual(segunda["estado"], "DUPLICADA")
        self.assertEqual(segunda["id_venta"], primera["id_venta"])
        self.assertEqual(PosSale.objects.filter(id_sucursal=self.sucursal).count(), 1)
        self.assertEqual(self.stock(), 4)
        self.assertEqual(SyncOperacion.objects.get(uuid=operacion["uuid"]).reintentos, 1)

    def test_mismo_uuid_dos_veces_en_un_lote(self):
        """Si el mismo UUID viene dos veces en un envío, solo se registra una venta."""
        operacion = self.venta()
        resultados = self.enviar(self.cajero, URL_VENTAS, [operacion, operacion])
        self.assertEqual([r["estado"] for r in resultados], ["SINCRONIZADA", "DUPLICADA"])
        self.assertEqual(PosSale.objects.filter(id_sucursal=self.sucursal).count(), 1)

    def test_venta_sin_stock_se_rechaza_y_queda_registrada(self):
        """Sin stock suficiente: RECHAZADA con motivo, sin venta y sin tocar el stock."""
        operacion = self.venta(cantidad=50)
        resultado = self.enviar(self.cajero, URL_VENTAS, [operacion])[0]
        self.assertEqual(resultado["estado"], "RECHAZADA")
        self.assertIn("Stock insuficiente", resultado["mensaje"])
        self.assertEqual(self.stock(), 5)
        self.assertFalse(PosSale.objects.filter(id_sucursal=self.sucursal).exists())
        guardada = SyncOperacion.objects.get(uuid=operacion["uuid"])
        self.assertEqual(guardada.estado, "RECHAZADA")
        reenvio = self.enviar(self.cajero, URL_VENTAS, [operacion])[0]
        self.assertEqual(reenvio["estado"], "RECHAZADA")
        self.assertFalse(PosSale.objects.filter(id_sucursal=self.sucursal).exists())

    def test_uuid_invalido_se_rechaza(self):
        """Una operación sin UUID válido se rechaza sin registrar nada."""
        resultado = self.enviar(self.cajero, URL_VENTAS, [self.venta(id_uuid="no-es-un-uuid")])[0]
        self.assertEqual(resultado["estado"], "RECHAZADA")
        self.assertFalse(PosSale.objects.filter(id_sucursal=self.sucursal).exists())

    # ---------------------------------------------------------------- reservas
    def test_reenviar_la_misma_reserva_no_la_duplica(self):
        """La reserva se crea una vez; el reenvío responde DUPLICADA y no descuenta otra vez."""
        operacion = self.reserva()
        primera = self.enviar(self.cliente, URL_RESERVAS, [operacion])[0]
        segunda = self.enviar(self.cliente, URL_RESERVAS, [operacion])[0]
        self.assertEqual(primera["estado"], "SINCRONIZADA")
        self.assertEqual(segunda["estado"], "DUPLICADA")
        self.assertEqual(segunda["id_reserva"], primera["id_reserva"])
        self.assertEqual(FittingReservation.objects.filter(id_sucursal=self.sucursal).count(), 1)
        self.assertEqual(self.stock(), 4)

    def test_reserva_sin_stock_se_rechaza(self):
        """Sin stock en la sucursal, la reserva se rechaza y no queda creada."""
        StockItem.objects.filter(id_sucursal=self.sucursal).update(cantidad=0)
        resultado = self.enviar(self.cliente, URL_RESERVAS, [self.reserva()])[0]
        self.assertEqual(resultado["estado"], "RECHAZADA")
        self.assertFalse(FittingReservation.objects.filter(id_sucursal=self.sucursal).exists())

    def test_solo_el_cliente_sincroniza_reservas(self):
        """El personal no puede usar el endpoint de reservas del cliente (403)."""
        respuesta = self.cajero.post(URL_RESERVAS, {"operaciones": [self.reserva()]}, format="json")
        self.assertEqual(respuesta.status_code, 403)