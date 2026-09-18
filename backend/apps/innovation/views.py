from rest_framework.viewsets import ModelViewSet

from common.permissions import IsCliente
from apps.users_auth.models import Cliente

from .models import ARTryOnSession
from .serializers import ARTryOnSessionSerializer


class ARTryOnSessionViewSet(ModelViewSet):
    """
    CU17 - Vestidor Virtual (AR 2D).

    Cada sesión deja registrado que un cliente probó un producto en
    el vestidor virtual (fecha + producto). El cliente solo ve y crea
    las suyas.
    """

    serializer_class = ARTryOnSessionSerializer
    permission_classes = [IsCliente]

    def get_queryset(self):
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        return ARTryOnSession.objects.filter(id_cliente=cliente).order_by("-fecha_sesion")

    def perform_create(self, serializer):
        cliente = Cliente.objects.get(id_usuario=self.request.user)
        serializer.save(id_cliente=cliente)