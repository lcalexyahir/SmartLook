"""Utilidades comunes: bitácora de auditoría e IP del cliente.

MODIFICADO (SaaS - bitácora de clientes): el cliente es global (no pertenece a
ninguna empresa), así que sus eventos quedaban sin empresa y el ADMIN_EMPRESA
no los veía en su bitácora (reservas, compras, devoluciones). Ahora, si el
usuario no tiene empresa, se toma la empresa del registro afectado
(reserva, orden, devolución, delivery o venta). También se puede indicar la
empresa directamente con el parámetro "empresa".
"""
import json
import logging

logger = logging.getLogger(__name__)

# Tabla afectada -> (app, modelo, campo con la empresa del registro).
MODELOS_CON_EMPRESA = {
    "fitting_reservation": ("reservations", "FittingReservation", "id_empresa"),
    "orders": ("sales", "Order", "id_empresa"),
    "devolucion": ("sales", "Devolucion", "id_empresa"),
    "delivery": ("sales", "Delivery", "id_orden__id_empresa"),
    "pos_sale": ("sales", "PosSale", "id_empresa"),
}


def empresa_del_registro(tabla_afectada, registro_id):
    """Id de la empresa dueña del registro afectado, o None si no se puede saber."""
    from django.apps import apps

    destino = MODELOS_CON_EMPRESA.get(tabla_afectada)
    if destino is None or not registro_id:
        return None
    app_label, nombre_modelo, campo = destino
    try:
        modelo = apps.get_model(app_label, nombre_modelo)
        return modelo.objects.filter(pk=registro_id).values_list(campo, flat=True).first()
    except Exception:
        return None


def log_audit(usuario, accion, tabla_afectada, registro_id, descripcion,
              datos_anterior=None, datos_nuevo=None, direccion_ip=None, empresa=None):
    """Registra un evento en la bitácora.

    La empresa del evento es, en orden: la indicada en "empresa", la del
    usuario (personal de una empresa) o la del registro afectado (eventos de
    clientes). Los eventos del SUPER_ADMIN sin registro asociado quedan sin
    empresa y solo los ve el SUPER_ADMIN.
    """
    from apps.users_auth.models import Bitacora
    try:
        autenticado = usuario if usuario and usuario.is_authenticated else None
        empresa_id = getattr(empresa, "pk", empresa)
        if empresa_id is None and autenticado is not None:
            empresa_id = autenticado.id_empresa_id
        if empresa_id is None:
            empresa_id = empresa_del_registro(tabla_afectada, registro_id)
        Bitacora.objects.create(
            id_usuario=autenticado,
            accion=accion,
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            descripcion=descripcion,
            datos_anterior=datos_anterior,
            datos_nuevo=datos_nuevo,
            direccion_ip=direccion_ip,
            id_empresa_id=empresa_id,
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