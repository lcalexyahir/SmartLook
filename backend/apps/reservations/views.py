from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from common.permissions import IsEncargadoSucursal, IsCliente
from common.utils import log_audit
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
            return queryset
        try:
            cliente = Cliente.objects.get(id_usuario=usuario)
        except Cliente.DoesNotExist:
            return queryset.none()
        return queryset.filter(id_cliente=cliente)

    def perform_create(self, serializer):
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        reserva = serializer.save(id_cliente=cliente)

        # NUEVO: registro legible en Bitácora, con nombre del cliente.
        log_audit(
            usuario=cliente.id_usuario,
            accion="RESERVA_CREADA",
            tabla_afectada="fitting_reservation",
            registro_id=reserva.id_reserva,
            descripcion=(
                f"{cliente.id_usuario.nombres} {cliente.id_usuario.apellidos} "
                f"reservó {reserva.items.count()} prenda(s) en "
                f"{reserva.id_sucursal.nombre} - Reserva #{reserva.id_reserva}"
            ),
        )

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        reserva = self.get_object()
        if reserva.estado == "COMPLETADA":
            return Response(
                {"error": "No se puede cancelar una reserva ya completada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reserva.estado = "CANCELADA"
        reserva.save()

        log_audit(
            usuario=request.user,
            accion="RESERVA_CANCELADA",
            tabla_afectada="fitting_reservation",
            registro_id=reserva.id_reserva,
            descripcion=f"{request.user.nombres} {request.user.apellidos} canceló la Reserva #{reserva.id_reserva}",
        )

        return Response(self.get_serializer(reserva).data)

    @action(detail=True, methods=["post"], permission_classes=[IsEncargadoSucursal])
    def confirmar(self, request, pk=None):
        reserva = self.get_object()
        reserva.estado = "CONFIRMADA"
        reserva.save()

        log_audit(
            usuario=request.user,
            accion="RESERVA_CONFIRMADA",
            tabla_afectada="fitting_reservation",
            registro_id=reserva.id_reserva,
            descripcion=(
                f"{request.user.nombres} {request.user.apellidos} confirmó la "
                f"Reserva #{reserva.id_reserva} del cliente {reserva.id_cliente}"
            ),
        )

        return Response(self.get_serializer(reserva).data)

    @action(detail=True, methods=["post"], permission_classes=[IsEncargadoSucursal])
    def completar(self, request, pk=None):
        reserva = self.get_object()
        reserva.estado = "COMPLETADA"
        reserva.save()

        log_audit(
            usuario=request.user,
            accion="RESERVA_COMPLETADA",
            tabla_afectada="fitting_reservation",
            registro_id=reserva.id_reserva,
            descripcion=(
                f"{request.user.nombres} {request.user.apellidos} completó la "
                f"Reserva #{reserva.id_reserva} del cliente {reserva.id_cliente}"
            ),
        )

        return Response(self.get_serializer(reserva).data)