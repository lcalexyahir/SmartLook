from django.db import models
from apps.users_auth.models import Usuario, Cliente
from apps.catalog.models import Sucursal, ProductoVariante


class FittingReservation(models.Model):
    id_reserva = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column="id_cliente")
    id_sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, db_column="id_sucursal")
    id_variante = models.ForeignKey(ProductoVariante, on_delete=models.CASCADE, db_column="id_variante")
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