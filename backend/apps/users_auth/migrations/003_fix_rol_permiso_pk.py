# apps/users_auth/migrations/0003_fix_rol_permiso_pk.py
#
# Mismo problema que 0002_fix_usuario_rol_pk.py, pero en la tabla
# "rol_permiso": PK compuesta (id_rol, id_permiso) no soportada por el ORM
# de Django 5.0, cuyo modelo RolPermiso tampoco declara primary_key
# explícita y por tanto espera una columna "id" autoincremental.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users_auth", "0002_fix_usuario_rol_pk"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                'ALTER TABLE rol_permiso ADD COLUMN id serial;',
                'ALTER TABLE rol_permiso DROP CONSTRAINT rol_permiso_pkey;',
                'ALTER TABLE rol_permiso ADD CONSTRAINT rol_permiso_pkey PRIMARY KEY (id);',
                'ALTER TABLE rol_permiso ADD CONSTRAINT rol_permiso_id_rol_id_permiso_uniq UNIQUE (id_rol, id_permiso);',
            ],
            reverse_sql=[
                'ALTER TABLE rol_permiso DROP CONSTRAINT rol_permiso_id_rol_id_permiso_uniq;',
                'ALTER TABLE rol_permiso DROP CONSTRAINT rol_permiso_pkey;',
                'ALTER TABLE rol_permiso ADD CONSTRAINT rol_permiso_pkey PRIMARY KEY (id_rol, id_permiso);',
                'ALTER TABLE rol_permiso DROP COLUMN id;',
            ],
        ),
    ]