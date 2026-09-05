from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FittingReservationViewSet

router = DefaultRouter()
router.register("reservas", FittingReservationViewSet, basename="reservas")

urlpatterns = [
    path("", include(router.urls)),
]