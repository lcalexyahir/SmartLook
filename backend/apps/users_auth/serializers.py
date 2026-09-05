from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from .models import Usuario, Cliente, Rol, Permiso, Bitacora


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ["id_rol", "nombre", "descripcion", "estado"]


class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = ["id_permiso", "nombre", "descripcion", "estado"]


class UsuarioSerializer(serializers.ModelSerializer):
    roles = RolSerializer(many=True, read_only=True)

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
            "roles",
        ]


class RegistroClienteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    direccion = serializers.CharField(required=False, allow_blank=True)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)

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
            "fecha_nacimiento",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        direccion = validated_data.pop("direccion", None)
        fecha_nacimiento = validated_data.pop("fecha_nacimiento", None)

        usuario = Usuario.objects.create(
            nombres=validated_data["nombres"],
            apellidos=validated_data["apellidos"],
            correo=validated_data["correo"],
            telefono=validated_data.get("telefono", ""),
            password_hash=make_password(validated_data["password"]),
            estado="ACTIVO",
        )

        rol_cliente = Rol.objects.get(nombre="CLIENTE")
        from .models import UsuarioRol
        UsuarioRol.objects.create(id_usuario=usuario, id_rol=rol_cliente)

        Cliente.objects.create(
            id_usuario=usuario,
            direccion=direccion,
            fecha_nacimiento=fecha_nacimiento,
        )

        return usuario


class LoginSerializer(serializers.Serializer):
    correo = serializers.EmailField()
    password = serializers.CharField(write_only=True)


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
            "fecha_evento",
        ]

    def get_usuario(self, obj):
        if obj.id_usuario:
            return f"{obj.id_usuario.nombres} {obj.id_usuario.apellidos}"
        return None