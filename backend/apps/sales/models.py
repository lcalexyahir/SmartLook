# backend/apps/sales/models.py
from django.db import models
from apps.users_auth.models import Empresa, Usuario, Cliente
from apps.catalog.models import Sucursal, ProductoVariante
from apps.reservations.models import FittingReservation, FittingReservationItem


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
    # NUEVO (SaaS): empresa del carrito. Como el cliente es global, cada
    # carrito pertenece a la empresa cuyos productos contiene (la asigna la
    # vista al crearlo; un cliente puede tener un carrito por empresa).
    id_empresa = models.ForeignKey(
        Empresa,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        db_column="id_empresa",
        related_name="carritos",
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
    # NUEVO (SaaS): empresa de la orden (heredada de la sucursal que la
    # atiende). Sus items, su delivery y sus devoluciones la heredan de aquí.
    id_empresa = models.ForeignKey(
        Empresa,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        db_column="id_empresa",
        related_name="ordenes",
    )

    class Meta:
        db_table = "orders"
        verbose_name = "Orden"
        verbose_name_plural = "Órdenes"

    def save(self, *args, **kwargs):
        """Hereda la empresa de la sucursal si no se indicó una."""
        if self.id_empresa_id is None and self.id_sucursal_id:
            self.id_empresa_id = self.id_sucursal.id_empresa_id
        super().save(*args, **kwargs)


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
        """Representación legible del delivery."""
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
    # NUEVO (SaaS): empresa de la venta POS (heredada de la sucursal).
    id_empresa = models.ForeignKey(
        Empresa,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        db_column="id_empresa",
        related_name="ventas_pos",
    )

    class Meta:
        db_table = "pos_sale"
        verbose_name = "Venta POS"
        verbose_name_plural = "Ventas POS"

    def save(self, *args, **kwargs):
        """Hereda la empresa de la sucursal si no se indicó una."""
        if self.id_empresa_id is None and self.id_sucursal_id:
            self.id_empresa_id = self.id_sucursal.id_empresa_id
        super().save(*args, **kwargs)


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
    # NUEVO (SaaS): empresa de la devolución (heredada de la orden).
    id_empresa = models.ForeignKey(
        Empresa,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        db_column="id_empresa",
        related_name="devoluciones",
    )

    class Meta:
        db_table = "devolucion"
        verbose_name = "Devolución"
        verbose_name_plural = "Devoluciones"

    def save(self, *args, **kwargs):
        """Hereda la empresa de la orden si no se indicó una."""
        if self.id_empresa_id is None and self.id_orden_id:
            self.id_empresa_id = self.id_orden.id_empresa_id
        super().save(*args, **kwargs)

    def __str__(self):
        """Representación legible de la devolución."""
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


# NUEVO (SaaS - paso 6): operaciones hechas SIN CONEXIÓN que el dispositivo
# envía al reconectarse. Cada operación trae un UUID generado en el
# dispositivo: si llega dos veces (reintento, red inestable), se reconoce
# por ese UUID y NO se registra de nuevo (idempotencia). Queda como
# historial, incluidas las rechazadas (ej. sin stock al sincronizar).
# NUEVO (SaaS - A.5): también registra las reservas de prendas que el
# cliente hizo sin conexión (tipo RESERVA, con la reserva creada).
class SyncOperacion(models.Model):
    TIPOS = [("VENTA_POS", "Venta presencial"), ("RESERVA", "Reserva de prendas")]
    ESTADOS = [
        ("RECIBIDA", "Recibida"),
        ("SINCRONIZADA", "Sincronizada"),
        ("RECHAZADA", "Rechazada"),
    ]
    id_operacion = models.AutoField(primary_key=True)
    # UUID generado en el dispositivo (clave de idempotencia).
    uuid = models.UUIDField(unique=True)
    tipo = models.CharField(max_length=30, choices=TIPOS, default="VENTA_POS")
    id_empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        db_column="id_empresa",
        related_name="operaciones_sync",
    )
    id_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="id_usuario",
        related_name="operaciones_sync",
    )
    # Datos tal como los envió el dispositivo (sucursal, método de pago, prendas).
    datos = models.JSONField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default="RECIBIDA")
    # Motivo del rechazo (ej. "Stock insuficiente...").
    mensaje = models.CharField(max_length=255, null=True, blank=True)
    # Venta creada al sincronizar (solo si quedó SINCRONIZADA).
    id_venta = models.OneToOneField(
        PosSale,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="id_venta",
        related_name="operacion_sync",
    )
    # NUEVO (SaaS - A.5): reserva creada al sincronizar (solo tipo RESERVA).
    id_reserva = models.OneToOneField(
        FittingReservation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="id_reserva",
        related_name="operacion_sync",
    )
    # Momento en que se hizo la operación en el dispositivo (sin conexión).
    fecha_operacion = models.DateTimeField(null=True, blank=True)
    fecha_recepcion = models.DateTimeField(auto_now_add=True)
    # Cuántas veces llegó repetida (reintentos ya procesados).
    reintentos = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "sync_operacion"
        verbose_name = "Operación sincronizada"
        verbose_name_plural = "Operaciones sincronizadas"
        indexes = [
            models.Index(fields=["id_empresa", "estado"], name="sync_op_empresa_estado_idx")
        ]

    def __str__(self):
        """Representación legible de la operación."""
        return f"{self.tipo} {self.uuid} ({self.estado})"