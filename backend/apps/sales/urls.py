from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, CartItemViewSet, OrderViewSet, PosSaleViewSet

router = DefaultRouter()
router.register("carritos", CartViewSet, basename="carritos")
router.register("carrito-items", CartItemViewSet, basename="carrito-items")
router.register("ordenes", OrderViewSet, basename="ordenes")
router.register("ventas-pos", PosSaleViewSet, basename="ventas-pos")

urlpatterns = [
    path("", include(router.urls)),
]