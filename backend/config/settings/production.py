"""Configuración de producción de SmartLook (Render + Neon)."""
import os
from urllib.parse import parse_qs, unquote, urlparse

from .base import *  # noqa: F401,F403


def _env_list(nombre):
    """Devuelve una variable de entorno separada por comas como lista."""
    return [v.strip() for v in os.getenv(nombre, "").split(",") if v.strip()]


def _database_desde_url(url):
    """Convierte DATABASE_URL (postgresql://...) en la config que espera Django."""
    partes = urlparse(url)
    query = parse_qs(partes.query)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": partes.path.lstrip("/"),
        "USER": unquote(partes.username or ""),
        "PASSWORD": unquote(partes.password or ""),
        "HOST": partes.hostname,
        "PORT": str(partes.port or 5432),
        "OPTIONS": {"sslmode": query.get("sslmode", ["require"])[0]},
    }


DEBUG = False

# Sin valor por defecto: si falta la variable, el arranque falla a propósito.
SECRET_KEY = os.environ["SECRET_KEY"]

# Hosts permitidos: variable ALLOWED_HOSTS + el host que Render inyecta solo.
ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS")
_render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if _render_host:
    ALLOWED_HOSTS.append(_render_host)

# Necesario para el login del admin de Django sobre HTTPS.
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS] + _env_list(
    "CSRF_TRUSTED_ORIGINS"
)

# Base de datos: si existe DATABASE_URL (Neon) se usa; si no, la de base.py.
_database_url = os.getenv("DATABASE_URL")
if _database_url:
    DATABASES = {"default": _database_desde_url(_database_url)}

# Archivos estáticos servidos por WhiteNoise (admin de Django, Swagger, etc.).
MIDDLEWARE = list(MIDDLEWARE)
_pos_security = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
MIDDLEWARE.insert(_pos_security + 1, "whitenoise.middleware.WhiteNoiseMiddleware")

STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# Seguridad. Render termina el HTTPS en su proxy y avisa con este header;
# sin la primera línea, SECURE_SSL_REDIRECT provoca un bucle de redirecciones.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"