from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaisViewSet,
    CiudadViewSet,
    SucursalViewSet,
    CategoriaViewSet,
    MarcaViewSet,
    TemporadaViewSet,
    ColeccionViewSet,
    ProductoViewSet,
    TallaViewSet,
    ColorViewSet,
    ProductoVarianteViewSet,
    ProveedorViewSet,
)

router = DefaultRouter()
router.register("paises", PaisViewSet, basename="paises")
router.register("ciudades", CiudadViewSet, basename="ciudades")
router.register("sucursales", SucursalViewSet, basename="sucursales")
router.register("categorias", CategoriaViewSet, basename="categorias")
router.register("marcas", MarcaViewSet, basename="marcas")
router.register("temporadas", TemporadaViewSet, basename="temporadas")
router.register("colecciones", ColeccionViewSet, basename="colecciones")
router.register("productos", ProductoViewSet, basename="productos")
router.register("tallas", TallaViewSet, basename="tallas")
router.register("colores", ColorViewSet, basename="colores")
router.register("variantes", ProductoVarianteViewSet, basename="variantes")
router.register("proveedores", ProveedorViewSet, basename="proveedores")

urlpatterns = [
    path("", include(router.urls)),
]