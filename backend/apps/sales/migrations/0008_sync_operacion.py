"""SaaS (paso 6): operaciones sin conexión sincronizadas (UUID, idempotencia, estados)."""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0007_empresa_multitenant"),
        ("users_auth", "0007_planes_suscripcion"),
    ]

    operations = [
        migrations.CreateModel(
            name="SyncOperacion",
            fields=[
                ("id_operacion", models.AutoField(primary_key=True, serialize=False)),
                ("uuid", models.UUIDField(unique=True)),
                (
                    "tipo",
                    models.CharField(
                        choices=[("VENTA_POS", "Venta presencial")],
                        default="VENTA_POS",
                        max_length=30,
                    ),
                ),
                ("datos", models.JSONField()),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("RECIBIDA", "Recibida"),
                            ("SINCRONIZADA", "Sincronizada"),
                            ("RECHAZADA", "Rechazada"),
                        ],
                        default="RECIBIDA",
                        max_length=20,
                    ),
                ),
                ("mensaje", models.CharField(blank=True, max_length=255, null=True)),
                ("fecha_operacion", models.DateTimeField(blank=True, null=True)),
                ("fecha_recepcion", models.DateTimeField(auto_now_add=True)),
                ("reintentos", models.PositiveIntegerField(default=0)),
                (
                    "id_empresa",
                    models.ForeignKey(
                        db_column="id_empresa",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operaciones_sync",
                        to="users_auth.empresa",
                    ),
                ),
                (
                    "id_usuario",
                    models.ForeignKey(
                        blank=True,
                        db_column="id_usuario",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="operaciones_sync",
                        to="users_auth.usuario",
                    ),
                ),
                (
                    "id_venta",
                    models.OneToOneField(
                        blank=True,
                        db_column="id_venta",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="operacion_sync",
                        to="sales.possale",
                    ),
                ),
            ],
            options={
                "verbose_name": "Operación sincronizada",
                "verbose_name_plural": "Operaciones sincronizadas",
                "db_table": "sync_operacion",
                "indexes": [
                    models.Index(
                        fields=["id_empresa", "estado"], name="sync_op_empresa_estado_idx"
                    )
                ],
            },
        ),
    ]