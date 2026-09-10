from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from drf_spectacular.utils import extend_schema

from common.permissions import IsAdminEmpresa
from .models import Usuario, Cliente, Rol, Permiso, Bitacora
from .serializers import (
    UsuarioSerializer,
    UsuarioCreateSerializer,
    UsuarioUpdateSerializer,
    RegistroClienteSerializer,
    LoginSerializer,
    RolSerializer,
    PermisoSerializer,
    BitacoraSerializer,
)
from .services import AuthService
from common.utils import log_audit


class RegistroClienteView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegistroClienteSerializer,
        responses={
            201: dict
        }
    )
    def post(self, request):
        serializer = RegistroClienteSerializer(data=request.data)

        if serializer.is_valid():
            usuario = serializer.save()

            log_audit(
                None,
                "REGISTRO",
                "usuarios",
                usuario.id_usuario,
                "Registro de cliente"
            )

            return Response(
                {
                    "message": "Cliente registrado exitosamente.",
                    "usuario_id": usuario.id_usuario
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: UsuarioSerializer
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():

            usuario = AuthService.autenticar_usuario(
                serializer.validated_data["correo"],
                serializer.validated_data["password"],
            )

            if usuario:

                tokens = AuthService.generar_tokens(usuario)

                log_audit(
                    usuario,
                    "LOGIN",
                    "usuarios",
                    usuario.id_usuario,
                    "Inicio de sesión"
                )

                return Response(
                    {
                        "tokens": tokens,
                        "usuario": UsuarioSerializer(usuario).data,
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                {
                    "error": "Credenciales inválidas."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class UsuarioViewSet(ModelViewSet):

    queryset = Usuario.objects.prefetch_related(
        "roles"
    ).all()


    permission_classes = [IsAdminEmpresa]


    def get_serializer_class(self):

        if self.action == "create":
            return UsuarioCreateSerializer


        if self.action in [
            "update",
            "partial_update"
        ]:
            return UsuarioUpdateSerializer


        return UsuarioSerializer


class RolViewSet(ReadOnlyModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]


class PermisoViewSet(ReadOnlyModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [IsAdminEmpresa]


class BitacoraViewSet(ReadOnlyModelViewSet):
    queryset = Bitacora.objects.all().order_by("-fecha_evento")
    serializer_class = BitacoraSerializer
    permission_classes = [IsAdminEmpresa]