from rest_framework.viewsets import ModelViewSet
from common.permissions import IsEncargadoSucursal
from .models import FittingReservation
from .serializers import FittingReservationSerializer


class FittingReservationViewSet(ModelViewSet):
    queryset = FittingReservation.objects.all()
    serializer_class = FittingReservationSerializer
    permission_classes = [IsEncargadoSucursal]