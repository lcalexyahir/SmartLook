from django.db import models
from apps.catalog.models import Sucursal, ProductoVariante
from apps.users_auth.models import Usuario


class StockItem(models.Model):
    id_stock = models.AutoField(primary_key=True)
    id_sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, db_column="id_sucursal")
    id_variante = models.ForeignKey(ProductoVariante, on_delete=models.CASCADE, db_column="id_variante")
    cantidad = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)
    stock_maximo = models.IntegerField(default=100)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stock_item"
        unique_together = ("id_sucursal", "id_variante")
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"

    def __str__(self):
        return f"{self.id_sucursal.nombre} - {self.id_variante} - {self.cantidad}"


class InventoryMovement(models.Model):
    id_movimiento = models.AutoField(primary_key=True)
    id_sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, db_column="id_sucursal")
    id_variante = models.ForeignKey(ProductoVariante, on_delete=models.CASCADE, db_column="id_variante")
    id_usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, db_column="id_usuario")
    tipo_movimiento = models.CharField(
        max_length=20,
        choices=[
            ("ENTRADA", "Entrada"),
            ("SALIDA", "Salida"),
            ("AJUSTE", "Ajuste"),
        ],
    )
    cantidad = models.IntegerField()
    motivo = models.CharField(max_length=255, null=True, blank=True)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_movement"
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"

    def __str__(self):
        return f"{self.tipo_movimiento} - {self.id_variante} - {self.cantidad}"