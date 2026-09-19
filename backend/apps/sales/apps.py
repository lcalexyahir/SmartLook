from django.apps import AppConfig
from django.db import DatabaseError
from django.db.models.signals import post_migrate


def crear_rol_repartidor(sender, **kwargs):
    """
    CU21: garantiza que el rol REPARTIDOR exista después de cada migrate
    (local y en Neon/Render). get_or_create no duplica si ya existe.
    """
    from apps.users_auth.models import Rol

    try:
        Rol.objects.get_or_create(
            nombre="REPARTIDOR",
            defaults={
                "descripcion": "Encargado de entregar los pedidos con delivery",
                "estado": True,
            },
        )
    except DatabaseError:
        # La tabla de roles aún no existe (migrate parcial): se ignora.
        pass


class SalesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sales"
    verbose_name = "Ventas"

    def ready(self):
        post_migrate.connect(crear_rol_repartidor, sender=self)