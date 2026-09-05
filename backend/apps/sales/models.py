from django.db import models
from apps.users_auth.models import Usuario, Cliente
from apps.catalog.models import Sucursal, ProductoVariante


class Cart(models.Model):
    id_carrito = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column="id_cliente")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(
        max_length=20,
        default="ACTIVO",
        choices=[("ACTIVO", "Activo"), ("ABANDONADO", "Abandonado"), ("CONVERTIDO", "Convertido")],
    )

    class Meta:
        db_table = "cart"
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"


class CartItem(models.Model):
    id_item = models.AutoField(primary_key=True)
    id_carrito = models.ForeignKey(Cart, on_delete=models.CASCADE, db_column="id_carrito")
    id_variante = models.ForeignKey(ProductoVariante, on_delete=models.CASCADE, db_column="id_variante")
    cantidad = models.IntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cart_item"
        verbose_name = "Item de Carrito"
        verbose_name_plural = "Items de Carrito"


class Order(models.Model):
    id_orden = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column="id_cliente")
    id_sucursal = models.ForeignKey(Sucursal, on_delete=models.RESTRICT, db_column="id_sucursal", null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20,
        default="PENDIENTE",
        choices=[
            ("PENDIENTE", "Pendiente"),
            ("PAGADA", "Pagada"),
            ("ENVIADA", "Enviada"),
            ("ENTREGADA", "Entregada"),
            ("CANCELADA", "Cancelada"),
        ],
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders"
        verbose_name = "Orden"
        verbose_name_plural = "Órdenes"


class OrderItem(models.Model):
    id_item = models.AutoField(primary_key=True)
    id_orden = models.ForeignKey(Order, on_delete=models.CASCADE, db_column="id_orden")
    id_variante = models.ForeignKey(ProductoVariante, on_delete=models.CASCADE, db_column="id_variante")
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "order_item"
        verbose_name = "Item de Orden"
        verbose_name_plural = "Items de Orden"


class PosSale(models.Model):
    id_venta = models.AutoField(primary_key=True)
    id_sucursal = models.ForeignKey(Sucursal, on_delete=models.RESTRICT, db_column="id_sucursal")
    id_usuario = models.ForeignKey(Usuario, on_delete=models.RESTRICT, db_column="id_usuario")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ("EFECTIVO", "Efectivo"),
            ("TARJETA", "Tarjeta"),
            ("QR", "QR"),
        ],
    )
    fecha_venta = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pos_sale"
        verbose_name = "Venta POS"
        verbose_name_plural = "Ventas POS"