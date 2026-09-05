from rest_framework import serializers
from .models import FittingReservation


class FittingReservationSerializer(serializers.ModelSerializer):
    cliente = serializers.StringRelatedField(source="id_cliente")
    sucursal = serializers.StringRelatedField(source="id_sucursal")
    variante = serializers.StringRelatedField(source="id_variante")

    class Meta:
        model = FittingReservation
        fields = [
            "id_reserva",
            "cliente",
            "sucursal",
            "variante",
            "fecha_reserva",
            "hora_reserva",
            "estado",
            "fecha_creacion",
        ]