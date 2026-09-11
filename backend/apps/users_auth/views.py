from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from django.db import transaction

from drf_spectacular.utils import extend_schema

from common.permissions import IsAdminEmpresa
from .models import Usuario, Cliente, Rol, Permiso, RolPermiso, Bitacora
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
from common.utils import log_audit, get_client_ip


class RegistroClienteView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

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
                "REGISTRO_CLIENTE",
                "clientes",
                usuario.id_usuario,
                f"Registro público de nuevo cliente: {usuario.correo}",
                datos_nuevo={
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "correo": usuario.correo,
                    "telefono": usuario.telefono,
                },
                direccion_ip=get_client_ip(request),
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
    authentication_classes = []

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
                    "Inicio de sesión",
                    direccion_ip=get_client_ip(request),
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

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtro opcional por rol, ej: /usuarios/?rol=CLIENTE
        # Usado por la pantalla de "Clientes" para listar solo usuarios
        # con rol CLIENTE (de solo lectura ahí, no se crean desde acá).
        rol = self.request.query_params.get("rol")
        if rol:
            queryset = queryset.filter(roles__nombre=rol)

        return queryset

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

    def get_permissions(self):
        if self.action == "permisos_asignados":
            return [IsAdminEmpresa()]
        return super().get_permissions()

    @action(detail=True, methods=["get", "put"], url_path="permisos")
    def permisos_asignados(self, request, pk=None):
        rol = self.get_object()

        if request.method == "GET":
            ids_asignados = list(
                RolPermiso.objects
                .filter(id_rol=rol)
                .values_list("id_permiso", flat=True)
            )
            return Response({"permisos": ids_asignados})

        ids_nuevos = request.data.get("permisos", [])

        with transaction.atomic():
            RolPermiso.objects.filter(id_rol=rol).delete()

            permisos_validos = Permiso.objects.filter(
                id_permiso__in=ids_nuevos
            )

            RolPermiso.objects.bulk_create([
                RolPermiso(id_rol=rol, id_permiso=permiso)
                for permiso in permisos_validos
            ])

        log_audit(
            request.user,
            "ACTUALIZAR_PERMISOS_ROL",
            "rol_permiso",
            rol.id_rol,
            f"Permisos actualizados para el rol {rol.nombre}",
            datos_nuevo={"permisos": list(ids_nuevos)},
            direccion_ip=get_client_ip(request),
        )

        return Response({
            "permisos": list(
                permisos_validos.values_list("id_permiso", flat=True)
            )
        })

class PermisoViewSet(ReadOnlyModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [IsAdminEmpresa]

class BitacoraViewSet(ReadOnlyModelViewSet):
    queryset = Bitacora.objects.all().order_by("-fecha_evento")
    serializer_class = BitacoraSerializer
    permission_classes = [IsAdminEmpresa]