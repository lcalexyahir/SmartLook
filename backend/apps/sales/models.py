# backend/apps/sales/models.py
from django.db import models
from apps.users_auth.models import Usuario, Cliente
from apps.catalog.models import Sucursal, ProductoVariante
from apps.reservations.models import FittingReservationItem


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
    id_reserva_item = models.ForeignKey(
        FittingReservationItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        unique=True,
        db_column="id_reserva_item",
        related_name="cart_item",
    )
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
    metodo_pago = models.CharField(
        max_length=20,
        default="TARJETA",
        choices=[("TARJETA", "Tarjeta"), ("QR", "QR")],
    )
    referencia_pago = models.CharField(max_length=100, null=True, blank=True)
    tipo_entrega = models.CharField(
        max_length=20,
        default="RETIRO",
        choices=[("RETIRO", "Retiro en sucursal"), ("DELIVERY", "Delivery a domicilio")],
    )
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders"
        verbose_name = "Orden"
        verbose_name_plural = "Órdenes"


class Delivery(models.Model):
    id_delivery = models.AutoField(primary_key=True)
    id_orden = models.OneToOneField(
        Order, on_delete=models.CASCADE, db_column="id_orden", related_name="delivery"
    )
    direccion = models.CharField(max_length=250)
    referencia = models.CharField(max_length=250, null=True, blank=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    distancia_km = models.DecimalField(max_digits=6, decimal_places=2)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20,
        default="PENDIENTE",
        choices=[
            ("PENDIENTE", "Pendiente"),
            ("EN_PREPARACION", "En preparación"),
            ("EN_CAMINO", "En camino"),
            ("ENTREGADO", "Entregado"),
        ],
    )
    id_repartidor = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="id_repartidor",
        related_name="entregas_asignadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_preparacion = models.DateTimeField(null=True, blank=True)
    fecha_en_camino = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "delivery"
        verbose_name = "Delivery"
        verbose_name_plural = "Deliveries"

    def __str__(self):
        return f"Delivery {self.id_delivery} - Orden {self.id_orden_id}"


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


class PosSaleItem(models.Model):
    id_item = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey(PosSale, on_delete=models.CASCADE, db_column="id_venta", related_name="items")
    id_variante = models.ForeignKey(ProductoVariante, on_delete=models.CASCADE, db_column="id_variante")
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    id_reserva_item = models.ForeignKey(
        FittingReservationItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        unique=True,
        db_column="id_reserva_item",
        related_name="pos_sale_item",
    )

    class Meta:
        db_table = "pos_sale_item"
        verbose_name = "Item de Venta POS"
        verbose_name_plural = "Items de Venta POS"


# NUEVO (devoluciones): el cliente devuelve prendas de un pedido con
# delivery ya entregado (ej. la sucursal se equivocó de talla/color). Se
# resuelve sola al pedirla, sin pasar por aprobación de un encargado, y
# repone el stock en la sucursal que despachó la orden. Mismo patrón
# cabecera/detalle que Order/OrderItem.
class Devolucion(models.Model):
    id_devolucion = models.AutoField(primary_key=True)
    id_orden = models.ForeignKey(
        Order, on_delete=models.CASCADE, db_column="id_orden", related_name="devoluciones"
    )
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column="id_cliente")
    estado = models.CharField(
        max_length=20,
        default="COMPLETADA",
        choices=[("COMPLETADA", "Completada")],
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "devolucion"
        verbose_name = "Devolución"
        verbose_name_plural = "Devoluciones"

    def __str__(self):
        return f"Devolución {self.id_devolucion} - Orden {self.id_orden_id}"


class DevolucionItem(models.Model):
    id_item = models.AutoField(primary_key=True)
    id_devolucion = models.ForeignKey(
        Devolucion, on_delete=models.CASCADE, db_column="id_devolucion", related_name="items"
    )
    id_orden_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, db_column="id_orden_item")
    cantidad = models.IntegerField()
    motivo = models.CharField(
        max_length=30,
        choices=[
            ("TALLA_INCORRECTA", "Talla incorrecta"),
            ("COLOR_INCORRECTO", "Color incorrecto"),
            ("PRODUCTO_DANADO", "Producto dañado/defectuoso"),
            ("OTRO", "Otro"),
        ],
    )

    class Meta:
        db_table = "devolucion_item"
        verbose_name = "Item de Devolución"
        verbose_name_plural = "Items de Devolución"