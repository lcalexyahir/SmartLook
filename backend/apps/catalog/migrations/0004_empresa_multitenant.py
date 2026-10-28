"""SaaS multitenant (paso 1): asocia las entidades del catálogo a una Empresa.

Categoría, marca, temporada, colección y proveedor dejan de tener nombre
único global y pasan a tenerlo único dentro de cada empresa. País,
Ciudad, Talla y Color siguen siendo catálogos globales.
"""
import django.db.models.deletion
from django.db import migrations, models

SLUG_EMPRESA_DEFECTO = "smartlook"


def asignar_empresa_por_defecto(apps, schema_editor):
    """Asigna la empresa por defecto a todo el catálogo existente."""
    Empresa = apps.get_model("users_auth", "Empresa")
    empresa = Empresa.objects.filter(slug=SLUG_EMPRESA_DEFECTO).first()
    if empresa is None:
        # Base de datos nueva: no hay datos previos que asignar.
        return
    apps.get_model("catalog", "Sucursal").objects.filter(
        id_empresa__isnull=True
    ).update(id_empresa=empresa)
    apps.get_model("catalog", "Categoria").objects.filter(
        id_empresa__isnull=True
    ).update(id_empresa=empresa)
    apps.get_model("catalog", "Marca").objects.filter(
        id_empresa__isnull=True
    ).update(id_empresa=empresa)
    apps.get_model("catalog", "Temporada").objects.filter(
        id_empresa__isnull=True
    ).update(id_empresa=empresa)
    apps.get_model("catalog", "Coleccion").objects.filter(
        id_empresa__isnull=True
    ).update(id_empresa=empresa)
    apps.get_model("catalog", "Producto").objects.filter(
        id_empresa__isnull=True
    ).update(id_empresa=empresa)
    apps.get_model("catalog", "Proveedor").objects.filter(
        id_empresa__isnull=True
    ).update(id_empresa=empresa)


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_sucursal_dias_atencion_sucursal_horario_atencion"),
        ("users_auth", "0005_empresa_multitenant"),
    ]

    operations = [
        migrations.AddField(
            model_name="sucursal",
            name="id_empresa",
            field=models.ForeignKey(
                blank=True,
                db_column="id_empresa",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="sucursales",
                to="users_auth.empresa",
            ),
        ),
        migrations.AddField(
            model_name="categoria",
            name="id_empresa",
            field=models.ForeignKey(
                blank=True,
                db_column="id_empresa",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="categorias",
                to="users_auth.empresa",
            ),
        ),
        migrations.AddField(
            model_name="marca",
            name="id_empresa",
            field=models.ForeignKey(
                blank=True,
                db_column="id_empresa",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="marcas",
                to="users_auth.empresa",
            ),
        ),
        migrations.AddField(
            model_name="temporada",
            name="id_empresa",
            field=models.ForeignKey(
                blank=True,
                db_column="id_empresa",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="temporadas",
                to="users_auth.empresa",
            ),
        ),
        migrations.AddField(
            model_name="coleccion",
            name="id_empresa",
            field=models.ForeignKey(
                blank=True,
                db_column="id_empresa",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="colecciones",
                to="users_auth.empresa",
            ),
        ),
        migrations.AddField(
            model_name="producto",
            name="id_empresa",
            field=models.ForeignKey(
                blank=True,
                db_column="id_empresa",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="productos",
                to="users_auth.empresa",
            ),
        ),
        migrations.AddField(
            model_name="proveedor",
            name="id_empresa",
            field=models.ForeignKey(
                blank=True,
                db_column="id_empresa",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="proveedores",
                to="users_auth.empresa",
            ),
        ),
        migrations.AlterField(
            model_name="categoria",
            name="nombre",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name="marca",
            name="nombre",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name="temporada",
            name="nombre",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name="coleccion",
            name="nombre",
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name="proveedor",
            name="nombre_empresa",
            field=models.CharField(max_length=150),
        ),
        migrations.AddConstraint(
            model_name="categoria",
            constraint=models.UniqueConstraint(
                fields=("id_empresa", "nombre"), name="uq_categoria_empresa_nombre"
            ),
        ),
        migrations.AddConstraint(
            model_name="marca",
            constraint=models.UniqueConstraint(
                fields=("id_empresa", "nombre"), name="uq_marca_empresa_nombre"
            ),
        ),
        migrations.AddConstraint(
            model_name="temporada",
            constraint=models.UniqueConstraint(
                fields=("id_empresa", "nombre"), name="uq_temporada_empresa_nombre"
            ),
        ),
        migrations.AddConstraint(
            model_name="coleccion",
            constraint=models.UniqueConstraint(
                fields=("id_empresa", "nombre"), name="uq_coleccion_empresa_nombre"
            ),
        ),
        migrations.AddConstraint(
            model_name="proveedor",
            constraint=models.UniqueConstraint(
                fields=("id_empresa", "nombre_empresa"), name="uq_proveedor_empresa_nombre"
            ),
        ),
        # Al final, para no alterar tablas con actualizaciones pendientes
        # en la misma transacción (PostgreSQL lo rechaza).
        migrations.RunPython(asignar_empresa_por_defecto, migrations.RunPython.noop),
    ]