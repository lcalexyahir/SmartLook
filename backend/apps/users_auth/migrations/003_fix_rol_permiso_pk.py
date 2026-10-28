# apps/users_auth/migrations/0003_fix_rol_permiso_pk.py
#
# Mismo problema que 0002_fix_usuario_rol_pk.py, pero en la tabla
# "rol_permiso": PK compuesta (id_rol, id_permiso) no soportada por el ORM
# de Django 5.0, cuyo modelo RolPermiso tampoco declara primary_key
# explícita y por tanto espera una columna "id" autoincremental.
#
# MODIFICADO (pruebas automáticas): solo hace el cambio si la columna "id"
# todavía no existe (en una base nueva 0001_initial ya la crea).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users_auth", "0002_fix_usuario_rol_pk"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = current_schema()
                          AND table_name = 'rol_permiso'
                          AND column_name = 'id'
                    ) THEN
                        ALTER TABLE rol_permiso ADD COLUMN id serial;
                        ALTER TABLE rol_permiso DROP CONSTRAINT rol_permiso_pkey;
                        ALTER TABLE rol_permiso ADD CONSTRAINT rol_permiso_pkey PRIMARY KEY (id);
                        ALTER TABLE rol_permiso ADD CONSTRAINT rol_permiso_id_rol_id_permiso_uniq
                            UNIQUE (id_rol, id_permiso);
                    END IF;
                END $$;
            """,
            reverse_sql=[
                'ALTER TABLE rol_permiso DROP CONSTRAINT rol_permiso_id_rol_id_permiso_uniq;',
                'ALTER TABLE rol_permiso DROP CONSTRAINT rol_permiso_pkey;',
                'ALTER TABLE rol_permiso ADD CONSTRAINT rol_permiso_pkey PRIMARY KEY (id_rol, id_permiso);',
                'ALTER TABLE rol_permiso DROP COLUMN id;',
            ],
        ),
    ]