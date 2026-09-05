from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Usuario


class SmartLookJWTAuthentication(JWTAuthentication):

    def get_user(self, validated_token):

        user_id = validated_token.get("user_id")

        if not user_id:
            raise AuthenticationFailed(
                "Token no contiene identificación de usuario"
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