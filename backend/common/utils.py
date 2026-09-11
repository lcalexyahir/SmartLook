import json
import logging

logger = logging.getLogger(__name__)


def log_audit(usuario, accion, tabla_afectada, registro_id, descripcion,
              datos_anterior=None, datos_nuevo=None, direccion_ip=None):
    from apps.users_auth.models import Bitacora

    try:
        Bitacora.objects.create(
            id_usuario=usuario if usuario and usuario.is_authenticated else None,
            accion=accion,
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            descripcion=descripcion,
            datos_anterior=datos_anterior,
            datos_nuevo=datos_nuevo,
            direccion_ip=direccion_ip,
        )
    except Exception as e:
        logger.error(f"Error al registrar bitácora: {e}")


def get_client_ip(request):
    """
    Extrae la IP real del cliente considerando el despliegue en la nube
    (proxy/balanceador), que suele reenviar la IP original en
    X-Forwarded-For.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")