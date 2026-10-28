from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from common.permissions import IsEncargadoSucursal, IsAdminEmpresaOrReadOnly
from common.tenancy import EmpresaScopedMixin, filtrar_queryset
from apps.catalog.models import Sucursal, ProductoVariante
from .models import StockItem, InventoryMovement
from .serializers import StockItemSerializer, InventoryMovementSerializer
from .services import StockService


class StockItemViewSet(EmpresaScopedMixin, ReadOnlyModelViewSet):
    # Antes: permission_classes = [IsEncargadoSucursal]
    # CU08 necesita que el cliente (incluso anónimo, el catálogo es público)
    # pueda consultar disponibilidad. Sigue siendo ReadOnly, así que no hay
    # riesgo de escritura sin permiso.
    # SaaS: el personal solo ve el stock de su empresa; el cliente ve el de
    # todas las empresas activas (catálogo unificado).
    serializer_class = StockItemSerializer
    permission_classes = [IsAdminEmpresaOrReadOnly]
    lectura_publica = True

    def get_queryset(self):
        """Stock activo dentro del alcance de empresa del usuario."""
        queryset = StockItem.objects.filter(estado=True).select_related(
            "id_sucursal", "id_sucursal__id_ciudad", "id_variante"
        )
        variante_id = self.request.query_params.get("variante")
        if variante_id:
            queryset = queryset.filter(id_variante_id=variante_id)
        return self.filtrar_por_empresa(queryset)


class InventoryMovementViewSet(EmpresaScopedMixin, ReadOnlyModelViewSet):
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsEncargadoSucursal]

    def get_queryset(self):
        """Movimientos de inventario de la empresa del usuario (privado)."""
        queryset = InventoryMovement.objects.all().order_by("-fecha_movimiento")
        return self.filtrar_por_empresa(queryset)


class MovementCreateView(APIView):
    permission_classes = [IsEncargadoSucursal]

    def post(self, request):
        """Registra un movimiento de stock solo con sucursal y variante de la empresa del usuario."""
        sucursal_id = request.data.get("id_sucursal")
        variante_id = request.data.get("id_variante")
        tipo = request.data.get("tipo_movimiento")
        cantidad = request.data.get("cantidad")
        motivo = request.data.get("motivo")

        if not all([sucursal_id, variante_id, tipo, cantidad]):
            return Response(
                {"error": "Faltan campos requeridos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # SaaS: la sucursal y la variante se buscan solo dentro de la empresa
        # del usuario; si son de otra empresa se responde como inexistentes.
        sucursales = filtrar_queryset(Sucursal.objects.all(), request)
        variantes = filtrar_queryset(
            ProductoVariante.objects.all(), request, campo="id_producto__id_empresa"
        )
        try:
            sucursal = sucursales.get(pk=sucursal_id)
            variante = variantes.get(pk=variante_id)
        except (Sucursal.DoesNotExist, ProductoVariante.DoesNotExist):
            return Response(
                {"error": "Sucursal o variante no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            movimiento = StockService.registrar_movimiento(
                sucursal=sucursal,
                variante=variante,
                usuario=request.user,
                tipo=tipo,
                cantidad=int(cantidad),
                motivo=motivo,
            )
            return Response(
                InventoryMovementSerializer(movimiento).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)