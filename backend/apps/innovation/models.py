from django.db import models
from apps.users_auth.models import Usuario, Cliente
from apps.catalog.models import Producto


class ARTryOnSession(models.Model):
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
    id_recomendacion = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column="id_cliente")
    productos_recomendados = models.JSONField()
    fecha_recomendacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendation_log"
        verbose_name = "Recomendación"
        verbose_name_plural = "Recomendaciones"


class ChatbotConversation(models.Model):
    id_conversacion = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column="id_cliente")
    mensaje_usuario = models.TextField()
    respuesta_bot = models.TextField()
    fecha_mensaje = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chatbot_conversation"
        verbose_name = "Conversación Chatbot"
        verbose_name_plural = "Conversaciones Chatbot"