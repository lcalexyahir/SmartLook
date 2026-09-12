from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from common.permissions import IsEncargadoSucursal, IsCliente
from apps.users_auth.models import Cliente
from .models import FittingReservation
from .serializers import FittingReservationSerializer


class FittingReservationViewSet(ModelViewSet):
    serializer_class = FittingReservationSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsCliente()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = FittingReservation.objects.all().order_by("-fecha_creacion")
        usuario = self.request.user
        es_encargado = usuario.roles.filter(
            nombre__in=["SUPER_ADMIN", "ADMIN_EMPRESA", "ENCARGADO_SUCURSAL"]
        ).exists()
        if es_encargado:
            # CU12: el encargado ve todas las reservas. El modelo actual no
            # asigna una sucursal específica a cada usuario encargado, así
            # que por ahora ve el listado completo (no solo su sucursal).
            return queryset
        # CU13: el cliente solo ve sus propias reservas.
        try:
            cliente = Cliente.objects.get(id_usuario=usuario)
        except Cliente.DoesNotExist:
            return queryset.none()
        return queryset.filter(id_cliente=cliente)

    def perform_create(self, serializer):
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        serializer.save(id_cliente=cliente)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        # get_object() ya filtra por get_queryset(), así que un cliente
        # solo puede llegar a cancelar SU propia reserva (una reserva
        # ajena le da 404, no 403 - no revela que existe).
        reserva = self.get_object()
        if reserva.estado == "COMPLETADA":
            return Response(
                {"error": "No se puede cancelar una reserva ya completada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reserva.estado = "CANCELADA"
        reserva.save()
        return Response(self.get_serializer(reserva).data)

    @action(detail=True, methods=["post"], permission_classes=[IsEncargadoSucursal])
    def confirmar(self, request, pk=None):
        reserva = self.get_object()
        reserva.estado = "CONFIRMADA"
        reserva.save()
        return Response(self.get_serializer(reserva).data)

    @action(detail=True, methods=["post"], permission_classes=[IsEncargadoSucursal])
    def completar(self, request, pk=None):
        reserva = self.get_object()
        reserva.estado = "COMPLETADA"
        reserva.save()
        return Response(self.get_serializer(reserva).data)