"""Crea los planes PLUS, PRO y ULTRA y asigna la suscripción de cada empresa.

Uso (después de migrate y seed_tenants):
    python manage.py seed_planes

- Crea los planes si no existen. Si ya existen, NO pisa sus precios ni
  límites: se configuran desde el admin o la API del SUPER_ADMIN.
- Cada empresa sin suscripción recibe el plan PRO por un semestre desde hoy
  (las 4 empresas actuales superan o pueden superar el límite de PLUS).
Es idempotente: se puede ejecutar varias veces (local y Neon).
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.users_auth.models import Empresa, PlanSuscripcion, Suscripcion
from apps.users_auth.suscripciones import TIPO_CAMBIO_BOB, en_bolivianos

# Límites: None = ilimitado.
PLANES = {
    "PLUS": {
        "nombre": "PLUS",
        "descripcion": "Hasta 2 sucursales, 5 usuarios y 50 productos. Sin delivery ni IA.",
        "precio_usd": Decimal("20.00"),
        "periodo": "MENSUAL",
        "max_sucursales": 2,
        "max_personal": 5,
        "max_productos": 50,
        "delivery": False,
        "vestidor_virtual": False,
        "chatbot_clientes": False,
        "reportes_ia": False,
        "comparativo_sucursales": True,
        "modo_offline": True,
    },
    "PRO": {
        "nombre": "PRO",
        "descripcion": "Hasta 10 sucursales, 30 usuarios y 500 productos, con IA y delivery.",
        "precio_usd": Decimal("100.00"),
        "periodo": "SEMESTRAL",
        "max_sucursales": 10,
        "max_personal": 30,
        "max_productos": 500,
        "delivery": True,
        "vestidor_virtual": True,
        "chatbot_clientes": True,
        "reportes_ia": True,
        "comparativo_sucursales": True,
        "modo_offline": True,
    },
    "ULTRA": {
        "nombre": "ULTRA",
        "descripcion": "Sucursales, usuarios y productos ilimitados, con todas las funciones.",
        "precio_usd": Decimal("200.00"),
        "periodo": "ANUAL",
        "max_sucursales": None,
        "max_personal": None,
        "max_productos": None,
        "delivery": True,
        "vestidor_virtual": True,
        "chatbot_clientes": True,
        "reportes_ia": True,
        "comparativo_sucursales": True,
        "modo_offline": True,
    },
}
PLAN_INICIAL = "PRO"


def _limite(valor):
    """Texto de un límite del plan (None = ilimitado)."""
    return "ilimitado" if valor is None else valor


class Command(BaseCommand):
    """Comando que deja configurados los planes y la suscripción de cada empresa."""

    help = "Crea los planes PLUS, PRO y ULTRA y asigna PRO a las empresas sin suscripción."

    @transaction.atomic
    def handle(self, *args, **options):
        """Crea planes y suscripciones, y muestra el resultado."""
        planes = {}
        for codigo, datos in PLANES.items():
            planes[codigo], _ = PlanSuscripcion.objects.get_or_create(
                codigo=codigo, defaults=datos
            )

        for empresa in Empresa.objects.filter(suscripcion__isnull=True):
            Suscripcion.objects.create(id_empresa=empresa, id_plan=planes[PLAN_INICIAL])

        self.stdout.write(self.style.SUCCESS(f"Planes (tipo de cambio: {TIPO_CAMBIO_BOB} Bs/USD):"))
        for plan in planes.values():
            self.stdout.write(
                f"  {plan.nombre}: USD {plan.precio_usd} / Bs {en_bolivianos(plan.precio_usd)} "
                f"({plan.get_periodo_display().lower()}) | sucursales {_limite(plan.max_sucursales)}"
                f" | personal {_limite(plan.max_personal)} | productos {_limite(plan.max_productos)}"
            )
        self.stdout.write(self.style.SUCCESS("Suscripciones:"))
        for s in Suscripcion.objects.select_related("id_empresa", "id_plan").order_by(
            "id_empresa__nombre"
        ):
            self.stdout.write(
                f"  {s.id_empresa.nombre}: {s.id_plan.nombre} | vence "
                f"{s.fecha_vencimiento:%d/%m/%Y} | {s.estado}"
            )