from django.db import models

from apps.catalog.models import Producto
from apps.users_auth.models import Cliente, Usuario


class ARTryOnSession(models.Model):
    """CU17: sesión de vestidor virtual de un cliente con un producto."""

    id_sesion = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column="id_cliente")
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column="id_producto")
    imagen_cliente = models.TextField(null=True, blank=True)
    resultado = models.TextField(null=True, blank=True)
    fecha_sesion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ar_tryon_session"
        verbose_name = "Sesión AR"
        verbose_name_plural = "Sesiones AR"


class RecommendationLog(models.Model):
    """CU18: prendas recomendadas a un cliente."""

    id_recomendacion = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column="id_cliente")
    productos_recomendados = models.JSONField()
    fecha_recomendacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendation_log"
        verbose_name = "Recomendación"
        verbose_name_plural = "Recomendaciones"


class ChatbotConversation(models.Model):
    """CU19: un intercambio del cliente con el asistente virtual."""

    id_conversacion = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column="id_cliente")
    mensaje_usuario = models.TextField()
    respuesta_bot = models.TextField()
    fecha_mensaje = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chatbot_conversation"
        verbose_name = "Conversación Chatbot"
        verbose_name_plural = "Conversaciones Chatbot"


class ReporteAsistente(models.Model):
    """CU20: reporte que el asistente de gestión generó para el personal.

    Se guarda el resultado completo para poder descargarlo de nuevo en PDF,
    Excel o HTML sin volver a consultar (ni a la IA).
    """

    id_reporte = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, db_column="id_usuario"
    )
    pregunta = models.TextField()
    consulta = models.CharField(max_length=50)
    filtros = models.JSONField(default=dict)
    titulo = models.CharField(max_length=200)
    resultado = models.JSONField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reporte_asistente"
        verbose_name = "Reporte del asistente"
        verbose_name_plural = "Reportes del asistente"