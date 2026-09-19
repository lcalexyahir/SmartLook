# backend/apps/sales/integrations/envio.py
#
# CU21 - Cálculo del costo de envío (delivery).
#   costo = tarifa_base + (km * tarifa_por_km) + recargo por prendas extra
# La distancia se pide a OpenRouteService (ruta real por calles). Si no hay
# clave, tarda o falla, se usa la línea recta (Haversine) x 1.3 como respaldo.
import math
from decimal import Decimal, ROUND_HALF_UP

import requests
from django.conf import settings

ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
ORS_TIMEOUT_SEG = 5
FACTOR_RUTA = 1.3  # la ruta por calles suele ser ~30% más larga que la línea recta


class EnvioError(Exception):
    pass


def distancia_haversine_km(lat1, lon1, lat2, lon2):
    """Distancia en línea recta entre dos puntos, en km."""
    lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    radio_tierra_km = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * radio_tierra_km * math.asin(math.sqrt(a))


def distancia_ruta_km(lat1, lon1, lat2, lon2):
    """
    Devuelve (km, fuente). fuente = "openrouteservice" o "linea_recta".
    OpenRouteService recibe las coordenadas como [longitud, latitud].
    """
    if settings.ORS_API_KEY:
        try:
            resp = requests.post(
                ORS_URL,
                headers={
                    "Authorization": settings.ORS_API_KEY,
                    "Content-Type": "application/json",
                },
                json={"coordinates": [[float(lon1), float(lat1)], [float(lon2), float(lat2)]]},
                timeout=ORS_TIMEOUT_SEG,
            )
            resp.raise_for_status()
            metros = resp.json()["routes"][0]["summary"]["distance"]
            return metros / 1000.0, "openrouteservice"
        except Exception:
            pass  # cualquier falla del servicio externo -> respaldo
    km = distancia_haversine_km(lat1, lon1, lat2, lon2) * FACTOR_RUTA
    return km, "linea_recta"


def calcular_costo_envio(distancia_km, cantidad_prendas):
    base = Decimal(str(settings.DELIVERY_TARIFA_BASE))
    por_km = Decimal(str(settings.DELIVERY_TARIFA_KM))
    recargo = Decimal(str(settings.DELIVERY_RECARGO_PRENDA))
    extra = max(0, int(cantidad_prendas) - settings.DELIVERY_PRENDAS_INCLUIDAS)
    costo = base + Decimal(str(distancia_km)) * por_km + recargo * extra
    return costo.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def cotizar(sucursal, latitud, longitud, cantidad_prendas):
    """
    Devuelve {"distancia_km", "costo_envio", "fuente_distancia"}.
    Lanza EnvioError si la sucursal no tiene coordenadas o el cliente queda
    fuera del radio máximo de reparto.
    """
    if sucursal.latitud is None or sucursal.longitud is None:
        raise EnvioError(f"La sucursal '{sucursal.nombre}' no tiene ubicación configurada.")

    en_linea_recta = distancia_haversine_km(
        sucursal.latitud, sucursal.longitud, latitud, longitud
    )
    if en_linea_recta > settings.DELIVERY_RADIO_MAX_KM:
        raise EnvioError(
            f"Tu ubicación está fuera del radio de reparto de {sucursal.nombre} "
            f"({settings.DELIVERY_RADIO_MAX_KM:g} km)."
        )

    km, fuente = distancia_ruta_km(sucursal.latitud, sucursal.longitud, latitud, longitud)
    km_dec = Decimal(str(km)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {
        "distancia_km": km_dec,
        "costo_envio": calcular_costo_envio(km_dec, cantidad_prendas),
        "fuente_distancia": fuente,
    }