from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from common.permissions import IsEncargadoSucursal
from apps.catalog.models import Sucursal, ProductoVariante
from .models import StockItem, InventoryMovement
from .serializers import StockItemSerializer, InventoryMovementSerializer
from .services import StockService

class StockItemViewSet(ReadOnlyModelViewSet):
    queryset = StockItem.objects.filter(estado=True)
    serializer_class = StockItemSerializer
    permission_classes = [IsEncargadoSucursal]

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

        # BUG ENCONTRADO Y CORREGIDO: antes esta vista llamaba a
        # StockService.registrar_movimiento(sucursal_id=..., variante_id=...),
        # pero el servicio espera las INSTANCIAS de Sucursal/ProductoVariante
        # bajo los nombres "sucursal"/"variante" (no "_id", no los IDs
        # crudos). Con la firma anterior, esta vista tronaba con un
        # TypeError apenas alguien intentaba registrar un movimiento.
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