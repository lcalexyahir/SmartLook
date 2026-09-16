from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Q

from common.permissions import IsAdminEmpresa, IsAdminEmpresaOrReadOnly
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


def _es_admin(request):
    usuario = request.user
    return usuario.is_authenticated and usuario.roles.filter(
        nombre__in=["SUPER_ADMIN", "ADMIN_EMPRESA"]
    ).exists()


class PaisViewSet(ReadOnlyModelViewSet):
    queryset = Pais.objects.filter(estado=True)
    serializer_class = PaisSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class CiudadViewSet(ModelViewSet):
    serializer_class = CiudadSerializer
    permission_classes = [IsAdminEmpresaOrReadOnly]

    def get_queryset(self):
        return Ciudad.objects.all() if _es_admin(self.request) else Ciudad.objects.filter(estado=True)

class SucursalViewSet(ModelViewSet):
    serializer_class = SucursalSerializer
    permission_classes = [IsAdminEmpresaOrReadOnly]

    def get_queryset(self):
        return Sucursal.objects.all() if _es_admin(self.request) else Sucursal.objects.filter(estado="ACTIVA")

class CategoriaViewSet(ModelViewSet):
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminEmpresaOrReadOnly]

    def get_queryset(self):
        return Categoria.objects.all() if _es_admin(self.request) else Categoria.objects.filter(estado=True)

class MarcaViewSet(ModelViewSet):
    serializer_class = MarcaSerializer
    permission_classes = [IsAdminEmpresaOrReadOnly]

    def get_queryset(self):
        return Marca.objects.all() if _es_admin(self.request) else Marca.objects.filter(estado=True)

class TemporadaViewSet(ModelViewSet):
    serializer_class = TemporadaSerializer
    permission_classes = [IsAdminEmpresaOrReadOnly]

    def get_queryset(self):
        return Temporada.objects.all() if _es_admin(self.request) else Temporada.objects.filter(estado=True)

class ColeccionViewSet(ModelViewSet):
    serializer_class = ColeccionSerializer
    permission_classes = [IsAdminEmpresaOrReadOnly]

    def get_queryset(self):
        return Coleccion.objects.all() if _es_admin(self.request) else Coleccion.objects.filter(estado=True)

class TallaViewSet(ModelViewSet):
    serializer_class = TallaSerializer
    permission_classes = [IsAdminEmpresaOrReadOnly]

    def get_queryset(self):
        return Talla.objects.all() if _es_admin(self.request) else Talla.objects.filter(estado=True)

class ColorViewSet(ModelViewSet):
    serializer_class = ColorSerializer
    permission_classes = [IsAdminEmpresaOrReadOnly]

    def get_queryset(self):
        return Color.objects.all() if _es_admin(self.request) else Color.objects.filter(estado=True)

class ProductoViewSet(ModelViewSet):
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminEmpresaOrReadOnly]

    def get_queryset(self):
        if _es_admin(self.request):
            queryset = Producto.objects.all().prefetch_related("productovariante_set")
        else:
            queryset = Producto.objects.filter(estado="ACTIVO").prefetch_related("productovariante_set")

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

class ProductoVarianteViewSet(ModelViewSet):
    serializer_class = ProductoVarianteSerializer
    permission_classes = [IsAdminEmpresaOrReadOnly]

    def get_queryset(self):
        if _es_admin(self.request):
            queryset = ProductoVariante.objects.all()
        else:
            queryset = ProductoVariante.objects.filter(estado__in=["DISPONIBLE", "AGOTADO"])

        busqueda = self.request.query_params.get("busqueda")
        if busqueda:
            queryset = queryset.filter(
                Q(codigo_producto__icontains=busqueda) | Q(id_producto__nombre__icontains=busqueda)
            )
        return queryset

class ProveedorViewSet(ModelViewSet):
    queryset = Proveedor.objects.filter(estado="ACTIVO")
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminEmpresa]