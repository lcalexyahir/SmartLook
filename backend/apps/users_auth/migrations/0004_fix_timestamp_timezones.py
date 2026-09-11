# apps/users_auth/migrations/0004_fix_timestamp_timezones.py
#
# CAUSA RAÍZ del "bug de la hora": el esquema original fue creado con SQL
# escrito a mano (no con migraciones de Django), y TODAS las columnas de
# fecha se declararon como "TIMESTAMP" (sin zona horaria) en vez de
# "TIMESTAMPTZ". Como consecuencia:
#   1. Postgres siempre guarda/lee esas columnas usando la zona horaria
#      de la SESIÓN (que en este servidor es UTC), sin importar qué
#      TIME_ZONE tenga Django en settings.
#   2. Django (USE_TZ=True) calcula la hora en UTC internamente (correcto)
#      y se la manda a Postgres, pero al guardarse en una columna sin
#      zona horaria, Postgres "pierde" la marca de que es UTC y deja los
#      números desnudos (ej: 22:19:46).
#   3. Al leer de vuelta, Django Rest Framework le pega la etiqueta
#      "-04:00" (por el TIME_ZONE = America/La_Paz) a esos números SIN
#      convertirlos - por eso el valor final queda mal por exactamente
#      4 horas, siempre.
#
# La solución correcta es cambiar el TIPO de columna a TIMESTAMPTZ,
# indicándole a Postgres explícitamente que los números que ya tiene
# guardados representan hora UTC (USING columna AT TIME ZONE 'UTC').
# Esto NO pierde ni modifica ningún dato: solo corrige la interpretación
# de la zona horaria, tanto para los registros viejos como para los
# nuevos que se guarden de ahora en adelante.

from django.db import migrations

COLUMNAS = [
    ("roles", "fecha_creacion"),
    ("permisos", "fecha_creacion"),
    ("rol_permiso", "fecha_asignacion"),
    ("usuarios", "ultimo_acceso"),
    ("usuarios", "fecha_creacion"),
    ("usuario_rol", "fecha_asignacion"),
    ("clientes", "fecha_registro"),
    ("pais", "fecha_creacion"),
    ("ciudad", "fecha_creacion"),
    ("sucursal", "fecha_creacion"),
    ("empleado", "fecha_creacion"),
    ("categoria", "fecha_creacion"),
    ("marca", "fecha_creacion"),
    ("temporada", "fecha_creacion"),
    ("coleccion", "fecha_creacion"),
    ("producto", "fecha_creacion"),
    ("producto_variante", "fecha_creacion"),
    ("proveedor", "fecha_creacion"),
    ("producto_proveedor", "fecha_asignacion"),
    ("bitacora", "fecha_evento"),
]

SQL_FORWARD = [
    f'ALTER TABLE {tabla} ALTER COLUMN {columna} '
    f"TYPE TIMESTAMPTZ USING {columna} AT TIME ZONE 'UTC';"
    for tabla, columna in COLUMNAS
]

SQL_REVERSE = [
    f'ALTER TABLE {tabla} ALTER COLUMN {columna} '
    f"TYPE TIMESTAMP USING {columna} AT TIME ZONE 'UTC';"
    for tabla, columna in COLUMNAS
]


class Migration(migrations.Migration):

    dependencies = [
        # OJO: el nombre real de ese archivo en el proyecto es
        # "003_fix_rol_permiso_pk.py" (sin el 0 inicial) - Django ya lo
        # registró como aplicado con ese nombre exacto, así que la
        # dependencia debe apuntar a ese nombre tal cual, no renombrarlo.
        ("users_auth", "003_fix_rol_permiso_pk"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]