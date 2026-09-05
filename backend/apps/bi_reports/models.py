from django.db import models
from apps.users_auth.models import Usuario


class ReportSnapshot(models.Model):
    id_reporte = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, db_column="id_usuario")
    tipo_reporte = models.CharField(max_length=50)
    parametros = models.JSONField(null=True, blank=True)
    archivo = models.TextField(null=True, blank=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "report_snapshot"
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"


class DashboardConfig(models.Model):
    id_config = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="id_usuario")
    configuracion = models.JSONField()
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dashboard_config"
        verbose_name = "Configuración Dashboard"
        verbose_name_plural = "Configuraciones Dashboard"