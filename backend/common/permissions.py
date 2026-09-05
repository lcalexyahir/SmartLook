from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.roles.filter(
            nombre="SUPER_ADMIN"
        ).exists()


class IsAdminEmpresa(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.roles.filter(
            nombre__in=["SUPER_ADMIN", "ADMIN_EMPRESA"]
        ).exists()


class IsEncargadoSucursal(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.roles.filter(
            nombre__in=["SUPER_ADMIN", "ADMIN_EMPRESA", "ENCARGADO_SUCURSAL"]
        ).exists()


class IsCajero(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.roles.filter(
            nombre__in=["SUPER_ADMIN", "ADMIN_EMPRESA", "ENCARGADO_SUCURSAL", "CAJERO"]
        ).exists()


class IsCliente(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.roles.filter(
            nombre="CLIENTE"
        ).exists()


class IsClienteOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return request.user.is_authenticated and request.user.roles.filter(
            nombre="CLIENTE"
        ).exists()