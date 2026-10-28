"""SaaS multitenant: los clientes pasan a ser globales a la plataforma.

Un cliente ya no pertenece a una empresa: con una sola cuenta puede
comprar y reservar en cualquier empresa. Se elimina Cliente.id_empresa y
los usuarios que solo tienen el rol CLIENTE quedan sin empresa.
"""
from django.db import migrations

ROLES_PERSONAL = ["SUPER_ADMIN", "ADMIN_EMPRESA", "ENCARGADO_SUCURSAL", "CAJERO", "REPARTIDOR"]


def liberar_clientes(apps, schema_editor):
    """Deja sin empresa a los usuarios que solo son clientes."""
    Usuario = apps.get_model("users_auth", "Usuario")
    ids_personal = Usuario.objects.filter(
        roles__nombre__in=ROLES_PERSONAL
    ).values_list("id_usuario", flat=True)
    Usuario.objects.filter(roles__nombre="CLIENTE").exclude(
        id_usuario__in=list(ids_personal)
    ).update(id_empresa=None, id_sucursal=None)


class Migration(migrations.Migration):

    dependencies = [
        ("users_auth", "0005_empresa_multitenant"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cliente",
            name="id_empresa",
        ),
        migrations.RunPython(liberar_clientes, migrations.RunPython.noop),
    ]