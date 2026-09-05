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

    class Meta:
        model = Ciudad
        fields = ["id_ciudad", "pais", "nombre", "estado"]


class SucursalSerializer(serializers.ModelSerializer):
    ciudad = CiudadSerializer(source="id_ciudad", read_only=True)

    class Meta:
        model = Sucursal
        fields = [
            "id_sucursal",
            "ciudad",
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
    talla = TallaSerializer(source="id_talla", read_only=True)
    color = ColorSerializer(source="id_color", read_only=True)

    class Meta:
        model = ProductoVariante
        fields = [
            "id_variante",
            "talla",
            "color",
            "codigo_producto",
            "precio",
            "cantidad",
            "imagen_variante",
            "estado",
        ]


class ProductoSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(source="id_categoria", read_only=True)
    marca = MarcaSerializer(source="id_marca", read_only=True)
    temporada = TemporadaSerializer(source="id_temporada", read_only=True)
    coleccion = ColeccionSerializer(source="id_coleccion", read_only=True)
    variantes = ProductoVarianteSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id_producto",
            "categoria",
            "marca",
            "temporada",
            "coleccion",
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