from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockItemViewSet, InventoryMovementViewSet, MovementCreateView

router = DefaultRouter()
router.register("stock", StockItemViewSet, basename="stock")
router.register("movimientos", InventoryMovementViewSet, basename="movimientos")

urlpatterns = [
    path("movimientos/registrar/", MovementCreateView.as_view(), name="registrar-movimiento"),
    path("", include(router.urls)),
]