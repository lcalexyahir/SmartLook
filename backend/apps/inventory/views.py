from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from common.permissions import IsEncargadoSucursal, IsAdminEmpresaOrReadOnly
from apps.catalog.models import Sucursal, ProductoVariante
from .models import StockItem, InventoryMovement
from .serializers import StockItemSerializer, InventoryMovementSerializer
from .services import StockService


class StockItemViewSet(ReadOnlyModelViewSet):
    # Antes: permission_classes = [IsEncargadoSucursal]
    # CU08 necesita que el cliente (incluso anónimo, el catálogo es público)
    # pueda consultar disponibilidad. Sigue siendo ReadOnly, así que no hay
    # riesgo de escritura sin permiso.
    serializer_class = StockItemSerializer
    permission_classes = [IsAdminEmpresaOrReadOnly]

    def get_queryset(self):
        queryset = StockItem.objects.filter(estado=True)
        variante_id = self.request.query_params.get("variante")
        if variante_id:
            queryset = queryset.filter(id_variante_id=variante_id)
        return queryset


class InventoryMovementViewSet(ReadOnlyModelViewSet):
    queryset = InventoryMovement.objects.all().order_by("-fecha_movimiento")
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsEncargadoSucursal]


class MovementCreateView(APIView):
    permission_classes = [IsEncargadoSucursal]

    def post(self, request):
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
        try:
            sucursal = Sucursal.objects.get(pk=sucursal_id)
            variante = ProductoVariante.objects.get(pk=variante_id)
        except (Sucursal.DoesNotExist, ProductoVariante.DoesNotExist):
            return Response(
                {"error": "Sucursal o variante no encontrada."},
                status=status.HTTP_400_BAD_REQUEST,
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