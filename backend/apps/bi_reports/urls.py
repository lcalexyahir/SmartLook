# apps/bi_reports/urls.py
#
# Archivo probablemente ya existe pero vacío (urlpatterns = []).
# Ya está incluido en config/urls.py bajo "api/bi/", así que este
# endpoint queda en: GET /api/bi/dashboard/

from django.urls import path
from .views import DashboardKpisView

urlpatterns = [
    path("dashboard/", DashboardKpisView.as_view(), name="dashboard-kpis"),
]