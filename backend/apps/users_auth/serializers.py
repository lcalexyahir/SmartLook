import re
from datetime import date

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.db import transaction

from .models import (
    Usuario,
    Cliente,
    Rol,
    Permiso,
    Bitacora
)


class RolSerializer(serializers.ModelSerializer):

    class Meta:
        model = Rol

        fields = [
            "id_rol",
            "nombre",
            "descripcion",
            "estado"
        ]


class PermisoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permiso

        fields = [
            "id_permiso",
            "nombre",
            "descripcion",
            "estado"
        ]


# ==========================
# LISTAR USUARIOS
# ==========================

class UsuarioSerializer(serializers.ModelSerializer):

    roles = RolSerializer(
        many=True,
        read_only=True
    )

    class Meta:

        model = Usuario

        fields = [
            "id_usuario",
            "nombres",
            "apellidos",
            "correo",
            "telefono",
            "estado",
            "ultimo_acceso",
            "fecha_creacion",
            "roles"
        ]


# ==========================
# CREAR USUARIOS
# ==========================

class UsuarioCreateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True
    )

    rol = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.all(),
        write_only=True
    )

    class Meta:

        model = Usuario

        fields = [
            "nombres",
            "apellidos",
            "correo",
            "telefono",
            "password",
            "rol"
        ]


    def create(self, validated_data):

        rol = validated_data.pop(
            "rol"
        )

        password = validated_data.pop(
            "password"
        )

        usuario = Usuario.objects.create(

            **validated_data,

            password_hash=make_password(
                password
            ),

            estado="ACTIVO"

        )

        from .models import UsuarioRol

        UsuarioRol.objects.create(

            id_usuario=usuario,

            id_rol=rol

        )

        return usuario


# ==========================
# EDITAR USUARIOS
# ==========================

class UsuarioUpdateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=False
    )

    rol = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.all(),
        write_only=True,
        required=False
    )

    class Meta:

        model = Usuario

        fields = [
            "nombres",
            "apellidos",
            "correo",
            "telefono",
            "password",
            "estado",
            "rol"
        ]


    def update(self, instance, validated_data):

        rol = validated_data.pop(
            "rol",
            None
        )

        password = validated_data.pop(
            "password",
            None
        )

        for campo, valor in validated_data.items():

            setattr(
                instance,
                campo,
                valor
            )

        if password:

            instance.password_hash = make_password(
                password
            )

        instance.save()


        if rol:

            from .models import UsuarioRol

            UsuarioRol.objects.filter(
                id_usuario=instance
            ).delete()

            UsuarioRol.objects.create(

                id_usuario=instance,

                id_rol=rol

            )

        return instance



# ==========================
# REGISTRO CLIENTE (CU01)
# ==========================

EDAD_MINIMA_CLIENTE = 13
# Bolivia: 8 dígitos, inicia en 6 o 7. Admite prefijo +591 opcional.
TELEFONO_REGEX = re.compile(r'^[67]\d{7}$')


class RegistroClienteSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    password_confirm = serializers.CharField(
        write_only=True
    )

    direccion = serializers.CharField(
        required=False,
        allow_blank=True
    )

    fecha_nacimiento = serializers.DateField(
        required=False,
        allow_null=True
    )

    class Meta:

        model = Usuario

        fields = [
            "nombres",
            "apellidos",
            "correo",
            "telefono",
            "password",
            "password_confirm",
            "direccion",
            "fecha_nacimiento"
        ]

    # ---- RN2: fortaleza de contraseña ----
    def validate_password(self, valor):
        if not re.search(r'[A-Za-z]', valor) or not re.search(r'\d', valor):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una letra y un número."
            )
        return valor

    # ---- RN7: formato de teléfono boliviano (solo si viene informado) ----
    def validate_telefono(self, valor):
        if not valor:
            return valor
        limpio = valor.strip().replace(" ", "").replace("-", "")
        if limpio.startswith("+591"):
            limpio = limpio[4:]
        elif limpio.startswith("591"):
            limpio = limpio[3:]
        if not TELEFONO_REGEX.match(limpio):
            raise serializers.ValidationError(
                "El teléfono debe tener 8 dígitos y comenzar con 6 o 7 "
                "(formato boliviano), con o sin prefijo +591."
            )
        return limpio

    # ---- RN8: cliente debe ser mayor de 13 años (solo si viene informado) ----
    def validate_fecha_nacimiento(self, valor):
        if valor is None:
            return valor
        hoy = date.today()
        edad = hoy.year - valor.year - (
            (hoy.month, hoy.day) < (valor.month, valor.day)
        )
        if edad < EDAD_MINIMA_CLIENTE:
            raise serializers.ValidationError(
                f"El cliente debe tener al menos {EDAD_MINIMA_CLIENTE} años."
            )
        return valor

    def validate(self, attrs):

        if attrs["password"] != attrs["password_confirm"]:

            raise serializers.ValidationError(
                {"password_confirm": "Las contraseñas no coinciden"}
            )

        return attrs


    def create(self, validated_data):

        validated_data.pop(
            "password_confirm"
        )

        direccion = validated_data.pop(
            "direccion",
            None
        )

        fecha = validated_data.pop(
            "fecha_nacimiento",
            None
        )

        # RN9: creación atómica de Usuario + Cliente + UsuarioRol
        with transaction.atomic():

            usuario = Usuario.objects.create(

                nombres=validated_data["nombres"],

                apellidos=validated_data["apellidos"],

                correo=validated_data["correo"],

                telefono=validated_data.get(
                    "telefono",
                    ""
                ),

                password_hash=make_password(
                    validated_data["password"]
                ),

                estado="ACTIVO"

            )

            from .models import UsuarioRol

            # RN6: si el rol CLIENTE no existe, se crea en vez de fallar.
            rol_cliente, _creado = Rol.objects.get_or_create(
                nombre="CLIENTE",
                defaults={
                    "descripcion": (
                        "Rol asignado automáticamente a los usuarios que "
                        "se registran públicamente como clientes."
                    ),
                    "estado": True,
                },
            )

            UsuarioRol.objects.create(

                id_usuario=usuario,

                id_rol=rol_cliente

            )

            Cliente.objects.create(

                id_usuario=usuario,

                direccion=direccion,

                fecha_nacimiento=fecha

            )

        return usuario



class LoginSerializer(serializers.Serializer):

    correo = serializers.EmailField()

    password = serializers.CharField(
        write_only=True
    )



class BitacoraSerializer(serializers.ModelSerializer):

    usuario = serializers.SerializerMethodField()


    class Meta:

        model = Bitacora

        fields = [
            "id_bitacora",
            "usuario",
            "accion",
            "tabla_afectada",
            "registro_id",
            "descripcion",
            "datos_anterior",
            "datos_nuevo",
            "direccion_ip",
            "fecha_evento"
        ]


    def get_usuario(self, obj):

        if obj.id_usuario:

            return (
                f"{obj.id_usuario.nombres} "
                f"{obj.id_usuario.apellidos}"
            )

        return None