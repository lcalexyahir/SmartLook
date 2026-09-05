from .models import Usuario, Bitacora
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken


class AuthService:

    @staticmethod
    def autenticar_usuario(correo, password):
        try:
            usuario = Usuario.objects.get(
                correo=correo,
                estado="ACTIVO"
            )

            if check_password(password, usuario.password_hash):
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
        """

        refresh = RefreshToken()

        refresh["user_id"] = usuario.id_usuario
        refresh["correo"] = usuario.correo
        refresh["nombre"] = f"{usuario.nombres} {usuario.apellidos}"

        roles = usuario.roles.values_list(
            "nombre",
            flat=True
        )

        refresh["roles"] = list(roles)

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

        return Bitacora.objects.create(
            id_usuario=usuario if usuario else None,
            accion=accion,
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            descripcion=descripcion,
            datos_anterior=datos_anterior,
            datos_nuevo=datos_nuevo,
        )