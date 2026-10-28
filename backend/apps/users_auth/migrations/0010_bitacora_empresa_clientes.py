"""Completa la empresa de los eventos de bitácora hechos por clientes.

Antes, los eventos de los clientes (reservas, compras, devoluciones) quedaban
sin empresa porque el cliente no pertenece a ninguna. Esta migración les
asigna la empresa del registro afectado, igual que hace ahora log_audit().
Solo toca filas sin empresa; se puede volver a ejecutar sin efectos extra.
"""
from django.db import migrations

MODELOS_CON_EMPRESA = {
    "fitting_reservation": ("reservations", "FittingReservation", "id_empresa"),
    "orders": ("sales", "Order", "id_empresa"),
    "devolucion": ("sales", "Devolucion", "id_empresa"),
    "delivery": ("sales", "Delivery", "id_orden__id_empresa"),
    "pos_sale": ("sales", "PosSale", "id_empresa"),
}


def completar_empresa(apps, schema_editor):
    """Asigna a cada evento sin empresa la empresa de su registro afectado."""
    Bitacora = apps.get_model("users_auth", "Bitacora")
    for tabla, (app_label, nombre_modelo, campo) in MODELOS_CON_EMPRESA.items():
        modelo = apps.get_model(app_label, nombre_modelo)
        eventos = Bitacora.objects.filter(
            id_empresa__isnull=True, tabla_afectada=tabla, registro_id__isnull=False
        )
        ids = set(eventos.values_list("registro_id", flat=True))
        empresas = dict(modelo.objects.filter(pk__in=ids).values_list("pk", campo))
        for registro_id, empresa_id in empresas.items():
            if empresa_id is not None:
                eventos.filter(registro_id=registro_id).update(id_empresa_id=empresa_id)


class Migration(migrations.Migration):

    dependencies = [
        ("users_auth", "0009_empresa_logo_imagen"),
        ("reservations", "0004_empresa_multitenant"),
        ("sales", "0009_sync_operacion_reserva"),
    ]

    operations = [
        migrations.RunPython(completar_empresa, migrations.RunPython.noop),
    ]