from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import ARTryOnSessionViewSet

router = DefaultRouter()

router.register("ar-sessions", ARTryOnSessionViewSet, basename="ar-sessions")

urlpatterns = [
    path("", include(router.urls)),
]