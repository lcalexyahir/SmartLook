from rest_framework import serializers
from apps.catalog.models import Sucursal, ProductoVariante
from .models import FittingReservation, FittingReservationItem


class FittingReservationItemSerializer(serializers.ModelSerializer):
    variante = serializers.StringRelatedField(source="id_variante", read_only=True)
    id_variante = serializers.PrimaryKeyRelatedField(
        queryset=ProductoVariante.objects.all(), write_only=True
    )

    class Meta:
        model = FittingReservationItem
        fields = ["id_item", "variante", "id_variante"]


class FittingReservationSerializer(serializers.ModelSerializer):
    # BUG ENCONTRADO Y CORREGIDO (CU11): "cliente"/"sucursal" eran
    # StringRelatedField de solo lectura sin ningún campo escribible
    # equivalente - no había forma de crear una reserva desde afuera.
    cliente = serializers.StringRelatedField(source="id_cliente", read_only=True)
    sucursal = serializers.StringRelatedField(source="id_sucursal", read_only=True)
    id_sucursal = serializers.PrimaryKeyRelatedField(
        queryset=Sucursal.objects.all(), write_only=True
    )
    # "items" no lleva source: coincide a propósito con el related_name="items"
    # puesto en FittingReservationItem.id_reserva.
    items = FittingReservationItemSerializer(many=True)

    class Meta:
        model = FittingReservation
        fields = [
            "id_reserva",
            "cliente",
            "sucursal",
            "id_sucursal",
            "fecha_reserva",
            "hora_reserva",
            "estado",
            "fecha_creacion",
            "items",
        ]
        read_only_fields = ["estado"]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("La reserva debe incluir al menos una prenda.")
        return value

    def create(self, validated_data):
        # "id_cliente" llega inyectado desde perform_create() en la vista
        # (serializer.save(id_cliente=...)), no lo manda el cliente.
        items_data = validated_data.pop("items")
        reserva = FittingReservation.objects.create(**validated_data)
        for item in items_data:
            FittingReservationItem.objects.create(id_reserva=reserva, **item)
        return reserva