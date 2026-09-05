from django.contrib import admin
from .models import (
    Pais,
    Ciudad,
    Sucursal,
    Categoria,
    Marca,
    Temporada,
    Coleccion,
    Producto,
    Talla,
    Color,
    ProductoVariante,
    Proveedor,
    ProductoProveedor,
)

admin.site.register(Pais)
admin.site.register(Ciudad)
admin.site.register(Sucursal)
admin.site.register(Categoria)
admin.site.register(Marca)
admin.site.register(Temporada)
admin.site.register(Coleccion)
admin.site.register(Producto)
admin.site.register(Talla)
admin.site.register(Color)
admin.site.register(ProductoVariante)
admin.site.register(Proveedor)
admin.site.register(ProductoProveedor)