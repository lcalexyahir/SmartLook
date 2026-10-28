# apps/users_auth/migrations/0002_fix_usuario_rol_pk.py
#
# Corrige la incompatibilidad entre la tabla real "usuario_rol" (creada con
# clave primaria compuesta (id_usuario, id_rol), no soportada por el ORM de
# Django 5.0) y lo que el modelo UsuarioRol espera implícitamente: una
# columna "id" autoincremental como PK.
#
# No se modifica models.py: al no declarar ningún campo con
# primary_key=True, Django YA asume que existe una columna "id" - esta
# migración simplemente la crea en la base de datos real.
#
# La restricción de negocio "un usuario no puede tener el mismo rol dos
# veces" se preserva moviéndola a un UNIQUE constraint separado.
#
# MODIFICADO (pruebas automáticas): solo hace el cambio si la columna "id"
# todavía no existe. En una base nueva (por ejemplo la base de pruebas que
# crea "python manage.py test"), 0001_initial ya crea "id" como PK y la
# restricción UNIQUE, así que esta migración no hace nada. En las bases que
# ya la tenían aplicada no cambia nada (Django no vuelve a ejecutarla).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users_auth", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = current_schema()
                          AND table_name = 'usuario_rol'
                          AND column_name = 'id'
                    ) THEN
                        ALTER TABLE usuario_rol ADD COLUMN id serial;
                        ALTER TABLE usuario_rol DROP CONSTRAINT usuario_rol_pkey;
                        ALTER TABLE usuario_rol ADD CONSTRAINT usuario_rol_pkey PRIMARY KEY (id);
                        ALTER TABLE usuario_rol ADD CONSTRAINT usuario_rol_id_usuario_id_rol_uniq
                            UNIQUE (id_usuario, id_rol);
                    END IF;
                END $$;
            """,
            reverse_sql=[
                'ALTER TABLE usuario_rol DROP CONSTRAINT usuario_rol_id_usuario_id_rol_uniq;',
                'ALTER TABLE usuario_rol DROP CONSTRAINT usuario_rol_pkey;',
                'ALTER TABLE usuario_rol ADD CONSTRAINT usuario_rol_pkey PRIMARY KEY (id_usuario, id_rol);',
                'ALTER TABLE usuario_rol DROP COLUMN id;',
            ],
        ),
    ]