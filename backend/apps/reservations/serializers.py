# backend/apps/reservations/serializers.py
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
        # NUEVO (vínculo reserva-venta): "estado" (PENDIENTE/COMPRADO/
        # DEVUELTO) expuesto de solo lectura, para que web/mobile puedan
        # mostrar qué pasó con cada prenda de la reserva.
        fields = ["id_item", "variante", "id_variante", "estado"]
        read_only_fields = ["estado"]


class FittingReservationSerializer(serializers.ModelSerializer):
    # BUG ENCONTRADO Y CORREGIDO (CU11): "cliente"/"sucursal" eran
    # StringRelatedField de solo lectura sin ningún campo escribible
    # equivalente - no había forma de crear una reserva desde afuera.
    cliente = serializers.StringRelatedField(source="id_cliente", read_only=True)
    sucursal = serializers.StringRelatedField(source="id_sucursal", read_only=True)
    # NUEVO (SaaS): tienda (empresa) de la reserva.
    id_empresa = serializers.IntegerField(source="id_empresa_id", read_only=True)
    empresa_nombre = serializers.CharField(source="id_empresa.nombre", read_only=True)
    # SaaS: solo sucursales activas de empresas activas (el cliente es
    # global y puede reservar en cualquier empresa).
    id_sucursal = serializers.PrimaryKeyRelatedField(
        queryset=Sucursal.objects.filter(estado="ACTIVA", id_empresa__estado="ACTIVA"),
        write_only=True,
    )
    # "items" no lleva source: coincide a propósito con el related_name="items"
    # puesto en FittingReservationItem.id_reserva.
    items = FittingReservationItemSerializer(many=True)

    class Meta:
        model = FittingReservation
        fields = [
            "id_reserva",
            "id_empresa",
            "empresa_nombre",
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
        """La reserva debe tener al menos una prenda."""
        if not value:
            raise serializers.ValidationError("La reserva debe incluir al menos una prenda.")
        return value

    def validate(self, attrs):
        """SaaS: todas las prendas deben ser de la misma empresa que la sucursal."""
        sucursal = attrs.get("id_sucursal")
        for item in attrs.get("items", []):
            variante = item["id_variante"]
            if variante.id_producto.id_empresa_id != sucursal.id_empresa_id:
                raise serializers.ValidationError(
                    {"items": f"'{variante}' no se vende en {sucursal.nombre}."}
                )
        return attrs

    def create(self, validated_data):
        """Crea la reserva (con la empresa de la sucursal) y sus prendas."""
        # "id_cliente" llega inyectado desde perform_create() en la vista
        # (serializer.save(id_cliente=...)), no lo manda el cliente.
        items_data = validated_data.pop("items")
        validated_data["id_empresa_id"] = validated_data["id_sucursal"].id_empresa_id
        reserva = FittingReservation.objects.create(**validated_data)
        for item in items_data:
            FittingReservationItem.objects.create(id_reserva=reserva, **item)
        return reserva