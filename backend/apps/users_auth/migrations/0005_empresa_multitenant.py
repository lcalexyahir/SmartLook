"""SaaS multitenant (paso 1): crea Empresa y la asocia a Usuario, Cliente y Bitácora.

Todos los datos existentes se asignan a una "empresa por defecto"
(SmartLook), salvo los usuarios SUPER_ADMIN, que son operadores de la
plataforma y no pertenecen a ninguna empresa.
"""
import uuid

import django.db.models.deletion
from django.db import migrations, models

SLUG_EMPRESA_DEFECTO = "smartlook"


def crear_empresa_por_defecto(apps, schema_editor):
    """Crea la empresa por defecto y le asigna usuarios, clientes y bitácora existentes."""
    Empresa = apps.get_model("users_auth", "Empresa")
    Usuario = apps.get_model("users_auth", "Usuario")
    Cliente = apps.get_model("users_auth", "Cliente")
    Bitacora = apps.get_model("users_auth", "Bitacora")

    # Base de datos nueva (sin datos previos): no hace falta empresa por defecto.
    if not Usuario.objects.exists():
        return

    empresa, _creada = Empresa.objects.get_or_create(
        slug=SLUG_EMPRESA_DEFECTO,
        defaults={"nombre": "SmartLook", "estado": "ACTIVA"},
    )

    # Todos los usuarios, excepto SUPER_ADMIN, pasan a la empresa por defecto.
    ids_super_admin = Usuario.objects.filter(
        roles__nombre="SUPER_ADMIN"
    ).values_list("id_usuario", flat=True)
    Usuario.objects.filter(id_empresa__isnull=True).exclude(
        id_usuario__in=list(ids_super_admin)
    ).update(id_empresa=empresa)

    Cliente.objects.filter(id_empresa__isnull=True).update(id_empresa=empresa)

    # La bitácora hereda la empresa de su usuario (los eventos del
    # SUPER_ADMIN o anónimos quedan sin empresa).
    Bitacora.objects.filter(
        id_empresa__isnull=True, id_usuario__id_empresa=empresa
    ).update(id_empresa=empresa)

    # El administrador responsable es el primer ADMIN_EMPRESA existente.
    admin = (
        Usuario.objects.filter(roles__nombre="ADMIN_EMPRESA", id_empresa=empresa)
        .order_by("id_usuario")
        .first()
    )
    if admin and empresa.id_administrador_id is None:
        empresa.id_administrador = admin
        empresa.save(update_fields=["id_administrador"])


class Migration(migrations.Migration):

    dependencies = [
        ("users_auth", "0004_fix_timestamp_timezones"),
        ("catalog", "0003_sucursal_dias_atencion_sucursal_horario_atencion"),
    ]

    operations = [
        migrations.CreateModel(
            name="Empresa",
            fields=[
                ("id_empresa", models.AutoField(primary_key=True, serialize=False)),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("nombre", models.CharField(max_length=150, unique=True)),
                ("slug", models.SlugField(max_length=60, unique=True)),
                ("nit", models.CharField(blank=True, max_length=30, null=True)),
                ("correo_contacto", models.CharField(blank=True, max_length=150, null=True)),
                ("telefono", models.CharField(blank=True, max_length=20, null=True)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("ACTIVA", "Activa"),
                            ("SUSPENDIDA", "Suspendida"),
                            ("INACTIVA", "Inactiva"),
                        ],
                        default="ACTIVA",
                        max_length=20,
                    ),
                ),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                (
                    "id_administrador",
                    models.ForeignKey(
                        blank=True,
                        db_column="id_administrador",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="empresas_administradas",
                        to="users_auth.usuario",
                    ),
                ),
            ],
            options={
                "verbose_name": "Empresa",
                "verbose_name_plural": "Empresas",
                "db_table": "empresa",
            },
        ),
        migrations.AddField(
            model_name="usuario",
            name="id_empresa",
            field=models.ForeignKey(
                blank=True,
                db_column="id_empresa",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="usuarios",
                to="users_auth.empresa",
            ),
        ),
        migrations.AddField(
            model_name="usuario",
            name="id_sucursal",
            field=models.ForeignKey(
                blank=True,
                db_column="id_sucursal",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="empleados",
                to="catalog.sucursal",
            ),
        ),
        migrations.AddField(
            model_name="cliente",
            name="id_empresa",
            field=models.ForeignKey(
                blank=True,
                db_column="id_empresa",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="clientes",
                to="users_auth.empresa",
            ),
        ),
        migrations.AddField(
            model_name="bitacora",
            name="id_empresa",
            field=models.ForeignKey(
                blank=True,
                db_column="id_empresa",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bitacoras",
                to="users_auth.empresa",
            ),
        ),
        migrations.RunPython(crear_empresa_por_defecto, migrations.RunPython.noop),
    ]