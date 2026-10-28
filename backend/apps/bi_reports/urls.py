# apps/bi_reports/urls.py
#
# Archivo probablemente ya existe pero vacío (urlpatterns = []).
# Ya está incluido en config/urls.py bajo "api/bi/", así que este
# endpoint queda en: GET /api/bi/dashboard/

from django.urls import path
from .views import DashboardKpisView

urlpatterns = [
    path("dashboard/", DashboardKpisView.as_view(), name="dashboard-kpis"),
]# apps/bi_reports/urls.py
#
# Incluido en config/urls.py bajo "api/bi/":
#   GET /api/bi/dashboard/                -> KPIs del dashboard
#   GET /api/bi/comparativo-sucursales/   -> NUEVO (paso 5): comparativo entre sucursales

from django.urls import path
from .views import ComparativoSucursalesView, DashboardKpisView

urlpatterns = [
    path("dashboard/", DashboardKpisView.as_view(), name="dashboard-kpis"),
    path(
        "comparativo-sucursales/",
        ComparativoSucursalesView.as_view(),
        name="comparativo-sucursales",
    ),
]