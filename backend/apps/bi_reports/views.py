# apps/bi_reports/views.py
#
# Archivo probablemente ya existe pero vacío/mínimo (la app bi_reports
# está registrada en INSTALLED_APPS y config/urls.py la incluye bajo
# "api/bi/", pero no tenía contenido real). Agrega el endpoint de KPIs
# del Dashboard, consumido tanto por la web como por mobile.

from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsAdminEmpresa
from apps.users_auth.models import Usuario
from apps.catalog.models import Producto, Sucursal, Proveedor
from apps.inventory.models import StockItem
from apps.sales.models import PosSale, Order
from apps.reservations.models import FittingReservation


class DashboardKpisView(APIView):
    """
    KPIs agregados para la pantalla de Dashboard (web y mobile).
    Solo admin/staff (no clientes) - mismos datos para ambas plataformas,
    un solo lugar de cálculo.
    """
    permission_classes = [IsAdminEmpresa]

    def get(self, request):
        total_clientes = Usuario.objects.filter(
            roles__nombre="CLIENTE",
            estado="ACTIVO",
        ).count()

        total_productos = Producto.objects.filter(estado="ACTIVO").count()
        total_sucursales = Sucursal.objects.filter(estado="ACTIVA").count()
        total_proveedores = Proveedor.objects.filter(estado="ACTIVO").count()

        stock_total = StockItem.objects.filter(estado=True).aggregate(
            total=Sum("cantidad")
        )["total"] or 0

        # Se compara contra un umbral fijo (5) en vez de comparar la
        # cantidad contra el stock_minimo de cada item (eso requeriría
        # F() para comparar dos columnas del mismo modelo) - se mantiene
        # simple para esta primera versión del dashboard.
        productos_stock_bajo = StockItem.objects.filter(
            estado=True,
            cantidad__lte=5,
        ).count()

        total_ventas_pos = PosSale.objects.count()
        monto_total_ventas = PosSale.objects.aggregate(
            total=Sum("total")
        )["total"] or 0

        total_ordenes = Order.objects.count()

        reservas_pendientes = FittingReservation.objects.filter(
            estado="PENDIENTE"
        ).count()

        return Response({
            "total_clientes": total_clientes,
            "total_productos": total_productos,
            "total_sucursales": total_sucursales,
            "total_proveedores": total_proveedores,
            "stock_total": stock_total,
            "productos_stock_bajo": productos_stock_bajo,
            "total_ventas_pos": total_ventas_pos,
            "monto_total_ventas": str(monto_total_ventas),
            "total_ordenes": total_ordenes,
            "reservas_pendientes": reservas_pendientes,
        })