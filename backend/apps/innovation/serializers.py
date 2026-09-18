from rest_framework import serializers

from .models import ARTryOnSession


class ARTryOnSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ARTryOnSession
        fields = [
            "id_sesion",
            "id_cliente",
            "id_producto",
            "imagen_cliente",
            "resultado",
            "fecha_sesion",
        ]
        read_only_fields = ["id_sesion", "id_cliente", "fecha_sesion"]