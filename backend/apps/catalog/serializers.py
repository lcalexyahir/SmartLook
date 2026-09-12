from rest_framework import serializers
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


class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = ["id_pais", "nombre", "estado"]


class CiudadSerializer(serializers.ModelSerializer):
    pais = PaisSerializer(source="id_pais", read_only=True)
    id_pais = serializers.PrimaryKeyRelatedField(
        queryset=Pais.objects.all(), write_only=True
    )

    class Meta:
        model = Ciudad
        fields = ["id_ciudad", "pais", "id_pais", "nombre", "estado"]


class SucursalSerializer(serializers.ModelSerializer):
    ciudad = CiudadSerializer(source="id_ciudad", read_only=True)
    id_ciudad = serializers.PrimaryKeyRelatedField(
        queryset=Ciudad.objects.all(), write_only=True
    )

    class Meta:
        model = Sucursal
        fields = [
            "id_sucursal",
            "ciudad",
            "id_ciudad",
            "nombre",
            "direccion",
            "telefono",
            "estado",
            "fecha_apertura",
        ]


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id_categoria", "nombre", "descripcion", "estado"]


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ["id_marca", "nombre", "descripcion", "estado"]


class TemporadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Temporada
        fields = ["id_temporada", "nombre", "descripcion", "fecha_inicio", "fecha_fin", "estado"]


class ColeccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coleccion
        fields = ["id_coleccion", "nombre", "descripcion", "anio", "estado"]


class TallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Talla
        fields = ["id_talla", "nombre", "descripcion", "estado"]


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ["id_color", "nombre", "codigo_hex", "estado"]


class ProductoVarianteSerializer(serializers.ModelSerializer):
    # "talla"/"color" de solo lectura (para mostrar el objeto completo en
    # GET). "id_talla"/"id_color"/"id_producto" son los campos escribibles
    # reales, usados en POST/PUT.
    # BUG ENCONTRADO Y CORREGIDO: no existía forma de indicar a qué
    # producto/talla/color pertenece una variante nueva.
    talla = TallaSerializer(source="id_talla", read_only=True)
    color = ColorSerializer(source="id_color", read_only=True)

    id_producto = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(), write_only=True
    )
    id_talla = serializers.PrimaryKeyRelatedField(
        queryset=Talla.objects.all(), write_only=True
    )
    id_color = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(), write_only=True
    )

    class Meta:
        model = ProductoVariante
        fields = [
            "id_variante",
            "id_producto",
            "talla",
            "id_talla",
            "color",
            "id_color",
            "codigo_producto",
            "precio",
            "cantidad",
            "imagen_variante",
            "estado",
        ]


class ProductoSerializer(serializers.ModelSerializer):
    # Mismo patrón: campos anidados de solo lectura + sus equivalentes
    # escribibles ("id_categoria" obligatorio; marca/temporada/colección
    # opcionales, igual que en el modelo).
    # BUG ENCONTRADO Y CORREGIDO: no existía forma de asignar categoría/
    # marca/temporada/colección al crear un producto.
    categoria = CategoriaSerializer(source="id_categoria", read_only=True)
    marca = MarcaSerializer(source="id_marca", read_only=True)
    temporada = TemporadaSerializer(source="id_temporada", read_only=True)
    coleccion = ColeccionSerializer(source="id_coleccion", read_only=True)

    # BUG ENCONTRADO Y CORREGIDO (CU08): faltaba el "source". Sin él, DRF
    # buscaba el atributo "variantes" en el modelo Producto, que no existe
    # (la relación inversa real, por no tener related_name en la FK de
    # ProductoVariante.id_producto, es "productovariante_set" - se ve en
    # catalog/views.py: prefetch_related("productovariante_set")).
    # Como el campo es read_only, DRF lo trataba como no-requerido y
    # descartaba el campo en silencio en vez de tronar toda la respuesta:
    # el producto cargaba bien, pero SIEMPRE sin variantes.
    variantes = ProductoVarianteSerializer(
        many=True, read_only=True, source="productovariante_set"
    )

    id_categoria = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), write_only=True
    )
    id_marca = serializers.PrimaryKeyRelatedField(
        queryset=Marca.objects.all(), write_only=True, required=False, allow_null=True
    )
    id_temporada = serializers.PrimaryKeyRelatedField(
        queryset=Temporada.objects.all(), write_only=True, required=False, allow_null=True
    )
    id_coleccion = serializers.PrimaryKeyRelatedField(
        queryset=Coleccion.objects.all(), write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Producto
        fields = [
            "id_producto",
            "categoria",
            "id_categoria",
            "marca",
            "id_marca",
            "temporada",
            "id_temporada",
            "coleccion",
            "id_coleccion",
            "nombre",
            "descripcion",
            "genero",
            "tipo_prenda",
            "imagen_producto",
            "modelo_virtual",
            "estado",
            "variantes",
        ]


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = [
            "id_proveedor",
            "nombre_empresa",
            "nombre_contacto",
            "telefono",
            "correo",
            "direccion",
            "estado",
        ]