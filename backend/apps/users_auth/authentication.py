from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Usuario


class SmartLookJWTAuthentication(JWTAuthentication):

    def get_user(self, validated_token):

        # El token de SmartLook guarda el id del usuario bajo la clave
        # "id_usuario" (ver services.py -> AuthService.generar_tokens),
        # no bajo "user_id" (que es el nombre por defecto de SimpleJWT).
        user_id = validated_token.get("id_usuario")

        if not user_id:
            raise AuthenticationFailed(
                "El token no contiene identificación de usuario"
            )

        try:
            usuario = Usuario.objects.get(
                id_usuario=user_id,
                estado="ACTIVO"
            )

        except Usuario.DoesNotExist:
            raise AuthenticationFailed(
                "Usuario no encontrado"
            )

        return usuario