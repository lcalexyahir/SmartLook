from .models import Usuario, Bitacora
from django.contrib.auth.hashers import check_password
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken


class AuthService:

    @staticmethod
    def autenticar_usuario(correo, password):
        """Devuelve el usuario si las credenciales son válidas, o None.

        NUEVO (SaaS): si las credenciales son correctas pero la empresa del
        usuario no está ACTIVA (suspendida o inactiva), se rechaza el ingreso
        con un mensaje claro en lugar de "credenciales inválidas".
        """
        try:
            usuario = Usuario.objects.select_related("id_empresa").get(
                correo=correo,
                estado="ACTIVO"
            )

            if check_password(password, usuario.password_hash):
                empresa = usuario.id_empresa
                if empresa is not None and empresa.estado != "ACTIVA":
                    raise AuthenticationFailed(
                        f"La empresa {empresa.nombre} no está activa en la plataforma."
                    )
                return usuario

        except Usuario.DoesNotExist:
            pass

        return None

    @staticmethod
    def generar_tokens(usuario):
        """
        Genera JWT para usuario personalizado de SmartLook.
        No utiliza RefreshToken.for_user()
        porque Usuario no hereda de AbstractUser.

        NUEVO (SaaS - paso 3): el token lleva también la empresa (tenant) y
        la sucursal del usuario. El backend las vuelve a comparar con la base
        de datos en cada petición (ver authentication.py). Para SUPER_ADMIN y
        clientes, que no pertenecen a una empresa, van en null.
        """

        refresh = RefreshToken()

        refresh["id_usuario"] = usuario.id_usuario
        refresh["correo"] = usuario.correo
        refresh["nombre"] = f"{usuario.nombres} {usuario.apellidos}"

        roles = usuario.roles.values_list(
            "nombre",
            flat=True
        )

        refresh["roles"] = list(roles)

        empresa = usuario.id_empresa
        refresh["id_empresa"] = usuario.id_empresa_id
        refresh["empresa"] = empresa.slug if empresa else None
        refresh["empresa_nombre"] = empresa.nombre if empresa else None
        refresh["id_sucursal"] = usuario.id_sucursal_id

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class AuditService:

    @staticmethod
    def registrar(
        usuario,
        accion,
        tabla_afectada,
        registro_id,
        descripcion,
        datos_anterior=None,
        datos_nuevo=None
    ):
        """Registra un evento en la bitácora."""

        return Bitacora.objects.create(
            id_usuario=usuario if usuario else None,
            accion=accion,
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            descripcion=descripcion,
            datos_anterior=datos_anterior,
            datos_nuevo=datos_nuevo,
        )