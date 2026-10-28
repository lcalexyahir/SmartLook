"""SaaS (paso 5): planes (PLUS, PRO, ULTRA), suscripción de cada empresa y pagos."""
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users_auth", "0006_clientes_globales"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlanSuscripcion",
            fields=[
                ("id_plan", models.AutoField(primary_key=True, serialize=False)),
                ("codigo", models.CharField(max_length=30, unique=True)),
                ("nombre", models.CharField(max_length=100)),
                ("descripcion", models.CharField(blank=True, max_length=255, null=True)),
                ("precio_usd", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "periodo",
                    models.CharField(
                        choices=[
                            ("MENSUAL", "Mensual"),
                            ("SEMESTRAL", "Semestral"),
                            ("ANUAL", "Anual"),
                        ],
                        default="MENSUAL",
                        max_length=20,
                    ),
                ),
                ("max_sucursales", models.PositiveIntegerField(blank=True, null=True)),
                ("max_personal", models.PositiveIntegerField(blank=True, null=True)),
                ("max_productos", models.PositiveIntegerField(blank=True, null=True)),
                ("delivery", models.BooleanField(default=False)),
                ("vestidor_virtual", models.BooleanField(default=False)),
                ("chatbot_clientes", models.BooleanField(default=False)),
                ("reportes_ia", models.BooleanField(default=False)),
                ("comparativo_sucursales", models.BooleanField(default=True)),
                ("modo_offline", models.BooleanField(default=True)),
                ("estado", models.BooleanField(default=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Plan de suscripción",
                "verbose_name_plural": "Planes de suscripción",
                "db_table": "plan_suscripcion",
            },
        ),
        migrations.CreateModel(
            name="Suscripcion",
            fields=[
                ("id_suscripcion", models.AutoField(primary_key=True, serialize=False)),
                (
                    "fecha_inicio",
                    models.DateField(default=django.utils.timezone.localdate),
                ),
                ("fecha_vencimiento", models.DateField(blank=True)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("ACTIVA", "Activa"),
                            ("VENCIDA", "Vencida"),
                            ("CANCELADA", "Cancelada"),
                        ],
                        default="ACTIVA",
                        max_length=20,
                    ),
                ),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                (
                    "id_empresa",
                    models.OneToOneField(
                        db_column="id_empresa",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suscripcion",
                        to="users_auth.empresa",
                    ),
                ),
                (
                    "id_plan",
                    models.ForeignKey(
                        db_column="id_plan",
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="suscripciones",
                        to="users_auth.plansuscripcion",
                    ),
                ),
            ],
            options={
                "verbose_name": "Suscripción",
                "verbose_name_plural": "Suscripciones",
                "db_table": "suscripcion",
            },
        ),
        migrations.CreateModel(
            name="PagoSuscripcion",
            fields=[
                ("id_pago", models.AutoField(primary_key=True, serialize=False)),
                ("monto_usd", models.DecimalField(decimal_places=2, max_digits=10)),
                ("monto_bob", models.DecimalField(decimal_places=2, max_digits=10)),
                ("tipo_cambio", models.DecimalField(decimal_places=2, max_digits=8)),
                ("referencia_pago", models.CharField(max_length=100, unique=True)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("PENDIENTE", "Pendiente"),
                            ("PAGADO", "Pagado"),
                            ("FALLIDO", "Fallido"),
                        ],
                        default="PENDIENTE",
                        max_length=20,
                    ),
                ),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_pago", models.DateTimeField(blank=True, null=True)),
                (
                    "id_empresa",
                    models.ForeignKey(
                        db_column="id_empresa",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pagos_suscripcion",
                        to="users_auth.empresa",
                    ),
                ),
                (
                    "id_plan",
                    models.ForeignKey(
                        db_column="id_plan",
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="pagos",
                        to="users_auth.plansuscripcion",
                    ),
                ),
                (
                    "id_usuario",
                    models.ForeignKey(
                        blank=True,
                        db_column="id_usuario",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="pagos_suscripcion",
                        to="users_auth.usuario",
                    ),
                ),
            ],
            options={
                "verbose_name": "Pago de suscripción",
                "verbose_name_plural": "Pagos de suscripción",
                "db_table": "pago_suscripcion",
            },
        ),
    ]