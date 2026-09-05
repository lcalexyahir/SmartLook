import json
import logging

logger = logging.getLogger(__name__)


def log_audit(usuario, accion, tabla_afectada, registro_id, descripcion, datos_anterior=None, datos_nuevo=None):
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
        )
    except Exception as e:
        logger.error(f"Error al registrar bitácora: {e}")