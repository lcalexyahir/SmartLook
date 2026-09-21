from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import ARTryOnSessionViewSet
from .views_chatbot import ChatbotHistorialView, ChatbotView

router = DefaultRouter()

router.register("ar-sessions", ARTryOnSessionViewSet, basename="ar-sessions")

urlpatterns = [
    # NUEVO (CU18/CU19): asistente virtual para el cliente.
    path("chatbot/", ChatbotView.as_view(), name="chatbot"),
    path("chatbot/historial/", ChatbotHistorialView.as_view(), name="chatbot-historial"),
    path("", include(router.urls)),
]