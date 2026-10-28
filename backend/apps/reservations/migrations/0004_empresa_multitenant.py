"""SaaS multitenant (paso 1): asocia las reservas de probador a una Empresa."""
import django.db.models.deletion
from django.db import migrations, models

SLUG_EMPRESA_DEFECTO = "smartlook"


def asignar_empresa_por_defecto(apps, schema_editor):
    """Asigna la empresa por defecto a las reservas existentes."""
    Empresa = apps.get_model("users_auth", "Empresa")
    empresa = Empresa.objects.filter(slug=SLUG_EMPRESA_DEFECTO).first()
    if empresa is None:
        # Base de datos nueva: no hay datos previos que asignar.
        return
    apps.get_model("reservations", "FittingReservation").objects.filter(
        id_empresa__isnull=True
    ).update(id_empresa=empresa)


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0003_fittingreservationitem_estado"),
        ("users_auth", "0005_empresa_multitenant"),
    ]

    operations = [
        migrations.AddField(
            model_name="fittingreservation",
            name="id_empresa",
            field=models.ForeignKey(
                blank=True,
                db_column="id_empresa",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="reservas",
                to="users_auth.empresa",
            ),
        ),
        # Al final, para no alterar tablas con actualizaciones pendientes
        # en la misma transacción (PostgreSQL lo rechaza).
        migrations.RunPython(asignar_empresa_por_defecto, migrations.RunPython.noop),
    ]