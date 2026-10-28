from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import SAFE_METHODS

from .models import Usuario
from .suscripciones import SuscripcionService, SuscripcionVencida

MENSAJE_SESION_CAMBIADA = (
    "Tu empresa o sucursal cambió desde que iniciaste sesión. "
    "Vuelve a iniciar sesión."
)

# NUEVO (SaaS - paso 5): con la suscripción vencida el personal todavía puede
# consultar (GET) y renovar o cambiar el plan; el resto de operaciones se bloquea.
RUTAS_PERMITIDAS_SIN_SUSCRIPCION = ("/api/auth/suscripciones/",)


class SmartLookJWTAuthentication(JWTAuthentication):
    """Autenticación JWT de SmartLook con validación del tenant (empresa).

    Además de validar la firma y la vigencia del token (lo hace SimpleJWT),
    en CADA petición protegida comprueba que:
    - el usuario exista y esté ACTIVO;
    - la empresa y la sucursal guardadas en el token sigan siendo las del
      usuario en la base de datos (si un administrador lo movió de empresa
      o de sucursal, el token anterior deja de servir);
    - la empresa del usuario siga ACTIVA (una empresa suspendida no opera);
    - (paso 5) si la suscripción de la empresa venció, solo se permiten
      consultas y la renovación o el cambio de plan.
    """

    def authenticate(self, request):
        """Autentica el token y bloquea operaciones de escritura con la suscripción vencida."""
        resultado = super().authenticate(request)
        if resultado is None:
            return None
        usuario, _token = resultado
        if (
            usuario.id_empresa_id is not None
            and request.method not in SAFE_METHODS
            and not request.path.startswith(RUTAS_PERMITIDAS_SIN_SUSCRIPCION)
            and not SuscripcionService.esta_vigente(usuario.id_empresa_id)
        ):
            raise SuscripcionVencida(
                f"La suscripción de {usuario.id_empresa.nombre} venció. "
                "Renueva el plan para seguir operando."
            )
        return resultado

    def get_user(self, validated_token):
        """Devuelve el usuario del token después de validar su empresa y sucursal."""
        # El token de SmartLook guarda el id del usuario bajo la clave
        # "id_usuario" (ver services.py -> AuthService.generar_tokens),
        # no bajo "user_id" (que es el nombre por defecto de SimpleJWT).
        user_id = validated_token.get("id_usuario")

        if not user_id:
            raise AuthenticationFailed(
                "El token no contiene identificación de usuario"
            )

        try:
            usuario = Usuario.objects.select_related("id_empresa").get(
                id_usuario=user_id,
                estado="ACTIVO"
            )

        except Usuario.DoesNotExist:
            raise AuthenticationFailed(
                "Usuario no encontrado"
            )

        # NUEVO (SaaS - paso 3): el tenant del token debe coincidir con el
        # de la base de datos. Los tokens emitidos antes de este cambio no
        # traen estas claves, así que obligan a iniciar sesión una vez más.
        if validated_token.get("id_empresa") != usuario.id_empresa_id:
            raise AuthenticationFailed(MENSAJE_SESION_CAMBIADA)
        if validated_token.get("id_sucursal") != usuario.id_sucursal_id:
            raise AuthenticationFailed(MENSAJE_SESION_CAMBIADA)

        empresa = usuario.id_empresa
        if empresa is not None and empresa.estado != "ACTIVA":
            raise AuthenticationFailed(
                f"La empresa {empresa.nombre} no está activa en la plataforma."
            )

        return usuario