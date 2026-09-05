from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from common.permissions import IsAdminEmpresa, IsClienteOrReadOnly
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
)
from .serializers import (
    PaisSerializer,
    CiudadSerializer,
    SucursalSerializer,
    CategoriaSerializer,
    MarcaSerializer,
    TemporadaSerializer,
    ColeccionSerializer,
    ProductoSerializer,
    TallaSerializer,
    ColorSerializer,
    ProductoVarianteSerializer,
    ProveedorSerializer,
)


class PaisViewSet(ReadOnlyModelViewSet):
    queryset = Pais.objects.filter(estado=True)
    serializer_class = PaisSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CiudadViewSet(ReadOnlyModelViewSet):
    queryset = Ciudad.objects.filter(estado=True)
    serializer_class = CiudadSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class SucursalViewSet(ReadOnlyModelViewSet):
    queryset = Sucursal.objects.filter(estado="ACTIVA")
    serializer_class = SucursalSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CategoriaViewSet(ReadOnlyModelViewSet):
    queryset = Categoria.objects.filter(estado=True)
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class MarcaViewSet(ReadOnlyModelViewSet):
    queryset = Marca.objects.filter(estado=True)
    serializer_class = MarcaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class TemporadaViewSet(ReadOnlyModelViewSet):
    queryset = Temporada.objects.filter(estado=True)
    serializer_class = TemporadaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ColeccionViewSet(ReadOnlyModelViewSet):
    queryset = Coleccion.objects.filter(estado=True)
    serializer_class = ColeccionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class TallaViewSet(ReadOnlyModelViewSet):
    queryset = Talla.objects.filter(estado=True)
    serializer_class = TallaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ColorViewSet(ReadOnlyModelViewSet):
    queryset = Color.objects.filter(estado=True)
    serializer_class = ColorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ProductoViewSet(ModelViewSet):
    queryset = Producto.objects.filter(estado="ACTIVO").prefetch_related("productovariante_set")
    serializer_class = ProductoSerializer
    permission_classes = [IsClienteOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        categoria = self.request.query_params.get("categoria")
        marca = self.request.query_params.get("marca")
        talla = self.request.query_params.get("talla")
        color = self.request.query_params.get("color")
        busqueda = self.request.query_params.get("busqueda")

        if categoria:
            queryset = queryset.filter(id_categoria__nombre=categoria)
        if marca:
            queryset = queryset.filter(id_marca__nombre=marca)
        if talla:
            queryset = queryset.filter(productovariante__id_talla__nombre=talla)
        if color:
            queryset = queryset.filter(productovariante__id_color__nombre=color)
        if busqueda:
            queryset = queryset.filter(nombre__icontains=busqueda)

        return queryset.distinct()


class ProductoVarianteViewSet(ReadOnlyModelViewSet):
    queryset = ProductoVariante.objects.filter(estado__in=["DISPONIBLE", "AGOTADO"])
    serializer_class = ProductoVarianteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ProveedorViewSet(ModelViewSet):
    queryset = Proveedor.objects.filter(estado="ACTIVO")
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminEmpresa]