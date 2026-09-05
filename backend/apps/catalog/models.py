from django.db import models


class Pais(models.Model):
    id_pais = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pais"
        verbose_name = "País"
        verbose_name_plural = "Países"

    def __str__(self):
        return self.nombre


class Ciudad(models.Model):
    id_ciudad = models.AutoField(primary_key=True)
    id_pais = models.ForeignKey(Pais, on_delete=models.RESTRICT, db_column="id_pais")
    nombre = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ciudad"
        verbose_name = "Ciudad"
        verbose_name_plural = "Ciudades"
        unique_together = ("id_pais", "nombre")

    def __str__(self):
        return self.nombre


class Sucursal(models.Model):
    id_sucursal = models.AutoField(primary_key=True)
    id_ciudad = models.ForeignKey(Ciudad, on_delete=models.RESTRICT, db_column="id_ciudad")
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=250)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        default="ACTIVA",
        choices=[("ACTIVA", "Activa"), ("INACTIVA", "Inactiva")],
    )
    fecha_apertura = models.DateField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sucursal"
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categoria"
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    id_marca = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "marca"
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

    def __str__(self):
        return self.nombre


class Temporada(models.Model):
    id_temporada = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "temporada"
        verbose_name = "Temporada"
        verbose_name_plural = "Temporadas"

    def __str__(self):
        return self.nombre


class Coleccion(models.Model):
    id_coleccion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    anio = models.IntegerField(null=True, blank=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "coleccion"
        verbose_name = "Colección"
        verbose_name_plural = "Colecciones"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(Categoria, on_delete=models.RESTRICT, db_column="id_categoria")
    id_marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True, db_column="id_marca")
    id_temporada = models.ForeignKey(Temporada, on_delete=models.SET_NULL, null=True, blank=True, db_column="id_temporada")
    id_coleccion = models.ForeignKey(Coleccion, on_delete=models.SET_NULL, null=True, blank=True, db_column="id_coleccion")
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(null=True, blank=True)
    genero = models.CharField(max_length=20, default="MASCULINO")
    tipo_prenda = models.CharField(max_length=50)
    imagen_producto = models.TextField(null=True, blank=True)
    modelo_virtual = models.TextField(null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        default="ACTIVO",
        choices=[("ACTIVO", "Activo"), ("INACTIVO", "Inactivo")],
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "producto"
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nombre


class Talla(models.Model):
    id_talla = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=20, unique=True)
    descripcion = models.CharField(max_length=100, null=True, blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "talla"
        verbose_name = "Talla"
        verbose_name_plural = "Tallas"

    def __str__(self):
        return self.nombre


class Color(models.Model):
    id_color = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    codigo_hex = models.CharField(max_length=10, null=True, blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "color"
        verbose_name = "Color"
        verbose_name_plural = "Colores"

    def __str__(self):
        return self.nombre


class ProductoVariante(models.Model):
    id_variante = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column="id_producto")
    id_talla = models.ForeignKey(Talla, on_delete=models.RESTRICT, db_column="id_talla")
    id_color = models.ForeignKey(Color, on_delete=models.RESTRICT, db_column="id_color")
    codigo_producto = models.CharField(max_length=50, unique=True, null=True, blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.IntegerField(default=0)
    imagen_variante = models.TextField(null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        default="DISPONIBLE",
        choices=[
            ("DISPONIBLE", "Disponible"),
            ("AGOTADO", "Agotado"),
            ("INACTIVO", "Inactivo"),
        ],
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "producto_variante"
        verbose_name = "Variante de Producto"
        verbose_name_plural = "Variantes de Productos"

    def __str__(self):
        return f"{self.id_producto.nombre} - {self.id_talla.nombre} - {self.id_color.nombre}"


class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    nombre_empresa = models.CharField(max_length=150, unique=True)
    nombre_contacto = models.CharField(max_length=100, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    correo = models.CharField(max_length=150, null=True, blank=True)
    direccion = models.CharField(max_length=250, null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        default="ACTIVO",
        choices=[("ACTIVO", "Activo"), ("INACTIVO", "Inactivo")],
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "proveedor"
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre_empresa


class ProductoProveedor(models.Model):
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column="id_producto")
    id_proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, db_column="id_proveedor")
    codigo_proveedor = models.CharField(max_length=100, null=True, blank=True)
    costo_compra = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "producto_proveedor"
        unique_together = ("id_producto", "id_proveedor")
        verbose_name = "Producto-Proveedor"
        verbose_name_plural = "Productos-Proveedores"