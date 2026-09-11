from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegistroClienteView,
    LoginView,
    UsuarioViewSet,
    RolViewSet,
    PermisoViewSet,
    BitacoraViewSet,
)

router = DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuarios")
router.register("roles", RolViewSet, basename="roles")
router.register("permisos", PermisoViewSet, basename="permisos")
router.register("bitacora", BitacoraViewSet, basename="bitacora")

urlpatterns = [
    path("registro/", RegistroClienteView.as_view(), name="registro"),
    path("login/", LoginView.as_view(), name="login"),
    path("", include(router.urls)),
]
