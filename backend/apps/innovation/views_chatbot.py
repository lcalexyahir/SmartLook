# backend/apps/innovation/views_chatbot.py
#
# NUEVO (CU18/CU19): endpoints del asistente virtual para el cliente.
#   POST /api/innovation/chatbot/            {"mensaje": "..."}
#   GET  /api/innovation/chatbot/historial/  últimos mensajes del cliente
#
# Solo el rol CLIENTE. El cliente se toma siempre del usuario autenticado
# (JWT): ningún dato del cuerpo de la petición decide de quién son los datos.

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users_auth.models import Cliente
from common.permissions import IsCliente

from .chatbot import MensajeInvalido, responder_cliente
from .llm import ServicioIANoDisponible
from .models import ChatbotConversation

HISTORIAL_MAXIMO = 30


def _cliente_de(request):
    return Cliente.objects.filter(id_usuario=request.user).first()


class ChatbotView(APIView):
    """CU19 - El cliente escribe una consulta y recibe la respuesta del asistente."""

    permission_classes = [IsCliente]

    def post(self, request):
        cliente = _cliente_de(request)
        if cliente is None:
            return Response(
                {"detail": "No se encontró el perfil de cliente."},
                status=status.HTTP_403_FORBIDDEN,
            )

        datos = request.data if isinstance(request.data, dict) else {}
        mensaje = datos.get("mensaje")
        if not isinstance(mensaje, str):
            mensaje = ""

        try:
            resultado = responder_cliente(cliente, mensaje)
        except MensajeInvalido as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ServicioIANoDisponible as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return Response(resultado)


class ChatbotHistorialView(APIView):
    """Últimos mensajes del cliente con el asistente, del más antiguo al más nuevo."""

    permission_classes = [IsCliente]

    def get(self, request):
        cliente = _cliente_de(request)
        if cliente is None:
            return Response(
                {"detail": "No se encontró el perfil de cliente."},
                status=status.HTTP_403_FORBIDDEN,
            )
        filas = list(
            ChatbotConversation.objects.filter(id_cliente=cliente).order_by(
                "-fecha_mensaje", "-id_conversacion"
            )[:HISTORIAL_MAXIMO]
        )
        filas.reverse()
        return Response(
            [
                {
                    "id": f.id_conversacion,
                    "mensaje": f.mensaje_usuario,
                    "respuesta": f.respuesta_bot,
                    "fecha": f.fecha_mensaje,
                }
                for f in filas
            ]
        )