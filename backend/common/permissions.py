from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        """Solo SUPER_ADMIN."""
        return request.user.is_authenticated and request.user.roles.filter(
            nombre="SUPER_ADMIN"
        ).exists()


class IsAdminEmpresa(BasePermission):
    def has_permission(self, request, view):
        """SUPER_ADMIN o ADMIN_EMPRESA."""
        return request.user.is_authenticated and request.user.roles.filter(
            nombre__in=["SUPER_ADMIN", "ADMIN_EMPRESA"]
        ).exists()


class IsEncargadoSucursal(BasePermission):
    def has_permission(self, request, view):
        """SUPER_ADMIN, ADMIN_EMPRESA o ENCARGADO_SUCURSAL."""
        return request.user.is_authenticated and request.user.roles.filter(
            nombre__in=["SUPER_ADMIN", "ADMIN_EMPRESA", "ENCARGADO_SUCURSAL"]
        ).exists()


class IsCajero(BasePermission):
    def has_permission(self, request, view):
        """Personal con acceso a caja (incluye roles superiores)."""
        return request.user.is_authenticated and request.user.roles.filter(
            nombre__in=["SUPER_ADMIN", "ADMIN_EMPRESA", "ENCARGADO_SUCURSAL", "CAJERO"]
        ).exists()


class IsCliente(BasePermission):
    def has_permission(self, request, view):
        """Solo CLIENTE."""
        return request.user.is_authenticated and request.user.roles.filter(
            nombre="CLIENTE"
        ).exists()


class IsClienteOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        """Lectura libre; escritura solo para CLIENTE."""
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return request.user.is_authenticated and request.user.roles.filter(
            nombre="CLIENTE"
        ).exists()


class IsAdminEmpresaOrReadOnly(BasePermission):
    """
    Lectura libre para cualquiera (incluye visitantes sin login, porque
    el catálogo web es público) - escritura (crear/editar/eliminar)
    solo para SUPER_ADMIN/ADMIN_EMPRESA.
    """
    def has_permission(self, request, view):
        """Lectura libre; escritura para SUPER_ADMIN/ADMIN_EMPRESA."""
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return request.user.is_authenticated and request.user.roles.filter(
            nombre__in=["SUPER_ADMIN", "ADMIN_EMPRESA"]
        ).exists()


class IsGlobalEditableSoloSuperAdmin(BasePermission):
    """
    NUEVO (SaaS): para catálogos GLOBALES compartidos por todas las
    empresas (País, Ciudad, Talla, Color). Lectura libre; crear un valor
    nuevo lo puede hacer SUPER_ADMIN o ADMIN_EMPRESA; editar o eliminar
    solo SUPER_ADMIN, porque el cambio afectaría a todas las empresas.
    """
    def has_permission(self, request, view):
        """Aplica las reglas de lectura, creación y edición descritas arriba."""
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        if not request.user.is_authenticated:
            return False
        roles = ["SUPER_ADMIN", "ADMIN_EMPRESA"] if request.method == "POST" else ["SUPER_ADMIN"]
        return request.user.roles.filter(nombre__in=roles).exists()


class IsRepartidor(BasePermission):
    def has_permission(self, request, view):
        """Personal con acceso a entregas (incluye roles superiores)."""
        return request.user.is_authenticated and request.user.roles.filter(
            nombre__in=["SUPER_ADMIN", "ADMIN_EMPRESA", "ENCARGADO_SUCURSAL", "REPARTIDOR"]
        ).exists()