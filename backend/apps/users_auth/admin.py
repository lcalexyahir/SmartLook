from django.contrib import admin
from .models import Rol, Permiso, RolPermiso, Usuario, UsuarioRol, Cliente, Bitacora

admin.site.register(Rol)
admin.site.register(Permiso)
admin.site.register(RolPermiso)
admin.site.register(Usuario)
admin.site.register(UsuarioRol)
admin.site.register(Cliente)
admin.site.register(Bitacora)