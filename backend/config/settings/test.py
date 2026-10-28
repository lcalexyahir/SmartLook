"""Configuración para las pruebas automáticas (python manage.py test).

Usa la misma configuración base del proyecto, pero la base de datos de
pruebas (test_<nombre>) se crea directamente desde los modelos actuales en
lugar de ejecutar todo el historial de migraciones. Algunas migraciones
antiguas se escribieron para corregir la base real de su momento y no
funcionan sobre una base vacía; las bases reales (local y Neon) no se ven
afectadas porque esta configuración solo se usa al correr las pruebas.

Uso:
    python manage.py test --settings=config.settings.test
"""
from .base import *  # noqa: F401,F403
from .base import DATABASES

DATABASES["default"]["TEST"] = {"MIGRATE": False}