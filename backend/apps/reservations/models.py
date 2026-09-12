from django.db import models
from apps.users_auth.models import Usuario, Cliente
from apps.catalog.models import Sucursal, ProductoVariante


class FittingReservation(models.Model):
    id_reserva = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column="id_cliente")
    id_sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, db_column="id_sucursal")
    # NOTA (CU11): "id_variante" se quitó de aquí. Antes una reserva solo
    # podía llevar UNA prenda. El enunciado (RF09) exige que el cliente
    # pueda reservar varias prendas a la vez, así que ahora esa relación
    # vive en FittingReservationItem (mismo patrón que Cart/CartItem en
    # la app sales).
    fecha_reserva = models.DateField()
    hora_reserva = models.TimeField()
    estado = models.CharField(
        max_length=20,
        default="PENDIENTE",
        choices=[
            ("PENDIENTE", "Pendiente"),
            ("CONFIRMADA", "Confirmada"),
            ("COMPLETADA", "Completada"),
            ("CANCELADA", "Cancelada"),
        ],
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fitting_reservation"
        verbose_name = "Reserva de Probador"
        verbose_name_plural = "Reservas de Probador"

    def __str__(self):
        return f"Reserva {self.id_reserva} - {self.id_cliente}"


class FittingReservationItem(models.Model):
    id_item = models.AutoField(primary_key=True)
    # related_name="items" explícito a propósito: el serializer expone el
    # campo "items" y necesita que el acceso inverso se llame exactamente
    # así (el mismo tipo de bug que corregimos en catalog/serializers.py
    # con "productovariante_set" vs "variantes" - esta vez lo dejamos bien
    # desde el modelo, sin depender de un "source" en el serializer).
    id_reserva = models.ForeignKey(
        FittingReservation, on_delete=models.CASCADE, db_column="id_reserva", related_name="items"
    )
    id_variante = models.ForeignKey(ProductoVariante, on_delete=models.CASCADE, db_column="id_variante")

    class Meta:
        db_table = "fitting_reservation_item"
        verbose_name = "Prenda de Reserva"
        verbose_name_plural = "Prendas de Reserva"

    def __str__(self):
        return f"Item {self.id_item} - Reserva {self.id_reserva_id}"