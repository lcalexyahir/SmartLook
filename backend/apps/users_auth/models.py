from django.db import models


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.nombre


class Permiso(models.Model):
    id_permiso = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "permisos"
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"

    def __str__(self):
        return self.nombre


class RolPermiso(models.Model):
    id_rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column="id_rol")
    id_permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, db_column="id_permiso")
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rol_permiso"
        unique_together = ("id_rol", "id_permiso")
        verbose_name = "Rol-Permiso"
        verbose_name_plural = "Roles-Permisos"


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    correo = models.CharField(max_length=150, unique=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    password_hash = models.TextField()
    estado = models.CharField(
        max_length=20,
        default="ACTIVO",
        choices=[
            ("ACTIVO", "Activo"),
            ("INACTIVO", "Inactivo"),
            ("BLOQUEADO", "Bloqueado"),
        ],
    )
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    roles = models.ManyToManyField(Rol, through="UsuarioRol", related_name="usuarios")

    class Meta:
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class UsuarioRol(models.Model):
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="id_usuario")
    id_rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column="id_rol")
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "usuario_rol"
        unique_together = ("id_usuario", "id_rol")
        verbose_name = "Usuario-Rol"
        verbose_name_plural = "Usuarios-Roles"


class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column="id_usuario")
    direccion = models.CharField(max_length=250, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "clientes"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"Cliente: {self.id_usuario.nombres} {self.id_usuario.apellidos}"


class Bitacora(models.Model):
    id_bitacora = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, db_column="id_usuario"
    )
    accion = models.CharField(max_length=50)
    tabla_afectada = models.CharField(max_length=100, null=True, blank=True)
    registro_id = models.IntegerField(null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    datos_anterior = models.JSONField(null=True, blank=True)
    datos_nuevo = models.JSONField(null=True, blank=True)
    direccion_ip = models.CharField(max_length=50, null=True, blank=True)
    fecha_evento = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bitacora"
        verbose_name = "Bitácora"
        verbose_name_plural = "Bitácoras"
        indexes = [
            models.Index(fields=["id_usuario"]),
            models.Index(fields=["fecha_evento"]),
            models.Index(fields=["tabla_afectada"]),
        ]

    def __str__(self):
        return f"{self.accion} - {self.tabla_afectada}"