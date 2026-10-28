"""Sincronización de operaciones hechas sin conexión (SaaS - paso 6).

Flujo:
1. Sin internet, el dispositivo (web PWA o móvil) guarda cada venta en su
   cola local con un UUID propio y el estado PENDIENTE.
2. Al reconectarse envía la cola a POST /api/sales/sync/ventas-pos/.
3. El servidor procesa cada operación por separado y responde un estado:
   - SINCRONIZADA: la venta se registró (stock descontado, bitácora).
   - DUPLICADA:    ese UUID ya se había sincronizado; NO se registra de
                   nuevo (idempotencia) y se devuelve la venta original.
   - RECHAZADA:    no se pudo registrar (ej. ya no hay stock); se guarda
                   el motivo para que el personal lo revise.
   El dispositivo quita de su cola las SINCRONIZADAS y DUPLICADAS.

Cada operación se procesa en su propia transacción: si una falla, las
demás del mismo lote siguen. Dos envíos simultáneos del mismo UUID no
crean dos ventas: la restricción UNIQUE del UUID en la base de datos
deja pasar solo uno.
"""
import uuid as uuid_lib

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import PosSale, SyncOperacion
from .services import PosSaleService

MAX_OPERACIONES_POR_LOTE = 100
METODOS_PAGO = ("EFECTIVO", "TARJETA", "QR")


class DatosInvalidos(Exception):
    """Los datos de la operación enviada no tienen el formato esperado."""


def _resultado(uuid, estado, mensaje=None, operacion=None):
    """Respuesta de una operación del lote."""
    venta = operacion.id_venta if operacion else None
    return {
        "uuid": str(uuid) if uuid else None,
        "estado": estado,
        "mensaje": mensaje,
        "id_venta": venta.id_venta if venta else None,
        "total": str(venta.total) if venta else None,
    }


def _resultado_existente(operacion):
    """Respuesta para un UUID que ya se había recibido (no se procesa otra vez)."""
    SyncOperacion.objects.filter(pk=operacion.pk).update(reintentos=F("reintentos") + 1)
    if operacion.estado == "SINCRONIZADA":
        return _resultado(
            operacion.uuid,
            "DUPLICADA",
            "Esta venta ya se había sincronizado; no se registró de nuevo.",
            operacion,
        )
    return _resultado(operacion.uuid, operacion.estado, operacion.mensaje, operacion)


def _leer_uuid(valor):
    """UUID enviado por el dispositivo, o None si no es válido."""
    try:
        return uuid_lib.UUID(str(valor))
    except (TypeError, ValueError, AttributeError):
        return None


def _leer_fecha(valor):
    """Fecha en que se hizo la operación sin conexión (nunca en el futuro)."""
    if not valor:
        return None
    fecha = parse_datetime(str(valor))
    if fecha is None:
        return None
    if timezone.is_naive(fecha):
        fecha = timezone.make_aware(fecha)
    return min(fecha, timezone.now())


def _leer_items(items):
    """Normaliza las prendas de la venta y valida sus cantidades."""
    if not isinstance(items, list) or not items:
        raise DatosInvalidos("La venta debe tener al menos una prenda.")
    normalizados = []
    for item in items:
        if not isinstance(item, dict):
            raise DatosInvalidos("Formato de prenda inválido.")
        if item.get("id_reserva_item"):
            if not str(item["id_reserva_item"]).isdigit():
                raise DatosInvalidos("Prenda reservada inválida.")
            normalizados.append({"id_reserva_item": int(item["id_reserva_item"]), "cantidad": 1})
            continue
        id_variante = item.get("id_variante")
        cantidad = item.get("cantidad")
        if not str(id_variante).isdigit():
            raise DatosInvalidos("Prenda inválida.")
        if not str(cantidad).isdigit() or int(cantidad) < 1:
            raise DatosInvalidos("La cantidad de cada prenda debe ser al menos 1.")
        normalizados.append({"id_variante": int(id_variante), "cantidad": int(cantidad)})
    return normalizados


class SyncService:
    """Procesa las operaciones sin conexión que llegan desde los dispositivos."""

    @staticmethod
    def sincronizar_ventas_pos(usuario, sucursales_permitidas, operaciones):
        """Procesa un lote de ventas POS hechas sin conexión.

        sucursales_permitidas: queryset de sucursales donde el usuario puede
        vender (ya filtrado por su empresa). Devuelve un resultado por
        operación, en el mismo orden en que llegaron.
        """
        return [
            SyncService._procesar_venta(usuario, sucursales_permitidas, operacion)
            for operacion in operaciones
        ]

    @staticmethod
    @transaction.atomic
    def _procesar_venta(usuario, sucursales_permitidas, datos):
        """Registra una venta sin conexión una sola vez por UUID."""
        if not isinstance(datos, dict):
            return _resultado(None, "RECHAZADA", "Formato de operación inválido.")
        uuid = _leer_uuid(datos.get("uuid"))
        if uuid is None:
            return _resultado(None, "RECHAZADA", "La operación no trae un UUID válido.")

        # 1) Idempotencia: si el UUID ya llegó antes, no se procesa otra vez.
        existente = SyncOperacion.objects.select_related("id_venta").filter(uuid=uuid).first()
        if existente is not None:
            if usuario.id_empresa_id and existente.id_empresa_id != usuario.id_empresa_id:
                return _resultado(uuid, "RECHAZADA", "Ese UUID ya pertenece a otra operación.")
            return _resultado_existente(existente)

        # 2) La sucursal debe ser de la empresa del usuario.
        id_sucursal = datos.get("id_sucursal")
        sucursal = None
        if str(id_sucursal).isdigit():
            sucursal = sucursales_permitidas.filter(pk=id_sucursal).first()
        empresa_id = sucursal.id_empresa_id if sucursal else usuario.id_empresa_id
        if empresa_id is None:
            return _resultado(uuid, "RECHAZADA", "Sucursal no encontrada.")

        # 3) Se guarda la operación (el UUID es UNIQUE: un envío simultáneo
        #    del mismo UUID falla aquí y se responde como duplicado).
        try:
            with transaction.atomic():
                operacion = SyncOperacion.objects.create(
                    uuid=uuid,
                    tipo="VENTA_POS",
                    id_empresa_id=empresa_id,
                    id_usuario=usuario,
                    datos={
                        "id_sucursal": id_sucursal,
                        "metodo_pago": datos.get("metodo_pago"),
                        "items": datos.get("items"),
                    },
                    fecha_operacion=_leer_fecha(datos.get("fecha_operacion")),
                )
        except IntegrityError:
            return _resultado_existente(
                SyncOperacion.objects.select_related("id_venta").get(uuid=uuid)
            )

        # 4) Se registra la venta con la misma lógica que una venta en línea.
        try:
            if sucursal is None:
                raise DatosInvalidos("Sucursal no encontrada.")
            metodo_pago = datos.get("metodo_pago")
            if metodo_pago not in METODOS_PAGO:
                raise DatosInvalidos("Método de pago inválido.")
            venta = PosSaleService.registrar_venta(
                usuario, sucursal, _leer_items(datos.get("items")), metodo_pago
            )
        except (DatosInvalidos, ValueError) as exc:
            operacion.estado = "RECHAZADA"
            operacion.mensaje = str(exc)[:255]
            operacion.save(update_fields=["estado", "mensaje"])
            return _resultado(uuid, "RECHAZADA", operacion.mensaje)

        # La venta conserva la hora en que se hizo sin conexión (reportes correctos).
        if operacion.fecha_operacion:
            PosSale.objects.filter(pk=venta.pk).update(fecha_venta=operacion.fecha_operacion)
        operacion.estado = "SINCRONIZADA"
        operacion.id_venta = venta
        operacion.save(update_fields=["estado", "id_venta"])
        return _resultado(uuid, "SINCRONIZADA", "Venta registrada.", operacion)