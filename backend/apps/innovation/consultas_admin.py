# backend/apps/innovation/consultas_admin.py

import logging
from datetime import date, timedelta

from django.db.models import Count, Sum
from django.utils import timezone

from apps.catalog.models import Sucursal
from apps.inventory.models import StockItem
from apps.reservations.models import FittingReservation
from apps.sales.models import Delivery, Order, OrderItem, PosSale, PosSaleItem

from .herramientas_cliente import (
    _coincide,
    _entero,
    _norm,
    _orden_talla,
    _palabras_utiles,
    _resolver,
    _tokens,
)
from .models import ARTryOnSession

logger = logging.getLogger(__name__)

ESTADOS_PAGADOS = ("PAGADA", "ENVIADA", "ENTREGADA")
MAX_FILAS = 500
LIMITE_TOP = 10
MAX_TOP = 50

ESTADOS_ENTREGA = {
    "PENDIENTE": "Pendiente",
    "EN_PREPARACION": "En preparación",
    "EN_CAMINO": "En camino",
    "ENTREGADO": "Entregado",
}
KPI_ENTREGA = {
    "PENDIENTE": "Pendientes",
    "EN_PREPARACION": "En preparación",
    "EN_CAMINO": "En camino",
    "ENTREGADO": "Entregadas",
}
ESTADOS_RESERVA = {
    "PENDIENTE": "Pendiente",
    "CONFIRMADA": "Confirmada",
    "COMPLETADA": "Completada",
    "CANCELADA": "Cancelada",
}
ALIAS_PERIODO = {
    "hoy": "hoy",
    "ayer": "ayer",
    "semana": "semana",
    "esta semana": "semana",
    "mes": "mes",
    "este mes": "mes",
    "mes_pasado": "mes_pasado",
    "mes pasado": "mes_pasado",
    "anio": "anio",
    "ano": "anio",
    "este ano": "anio",
    "todo": "todo",
    "siempre": "todo",
    "historico": "todo",
}
ALIAS_AGRUPAR = {
    "dia": "dia",
    "dias": "dia",
    "diario": "dia",
    "sucursal": "sucursal",
    "sucursales": "sucursal",
    "metodo": "metodo",
    "metodo_pago": "metodo",
    "metodo de pago": "metodo",
    "pago": "metodo",
    "canal": "canal",
    "canales": "canal",
}
GRUPOS_VENTAS = {
    "dia": "Día",
    "sucursal": "Sucursal",
    "metodo": "Método de pago",
    "canal": "Canal",
}


class ConsultaInvalida(Exception):
    """La consulta pedida no existe o no se pudo ejecutar."""


# ---------------------------------------------------------------- utilidades
def _fmt(d):
    """Fecha en formato dd/mm/aaaa."""
    return d.strftime("%d/%m/%Y")


def _fecha(valor):
    """Convierte 'AAAA-MM-DD' en date, o None si no es una fecha válida."""
    try:
        return date.fromisoformat(str(valor).strip()[:10])
    except (TypeError, ValueError):
        return None


def _verdadero(valor):
    """Interpreta true/'si'/1 como verdadero (los modelos a veces mandan texto)."""
    if isinstance(valor, bool):
        return valor
    return _norm(valor) in ("true", "si", "sí", "1", "yes")


def _dinero(valor):
    """Monto como float con dos decimales."""
    return round(float(valor or 0), 2)


def _rango(args, defecto="hoy", hoy=None):
    """Devuelve (desde, hasta, etiqueta) según periodo, desde y hasta.

    None en desde o hasta significa sin límite. Con 'desde'/'hasta' explícitos
    se ignora 'periodo'.
    """
    hoy = hoy or timezone.localdate()
    desde, hasta = _fecha(args.get("desde")), _fecha(args.get("hasta"))
    if desde or hasta:
        if desde and hasta and desde > hasta:
            desde, hasta = hasta, desde
        if desde and hasta:
            etiqueta = f"del {_fmt(desde)} al {_fmt(hasta)}"
        elif desde:
            etiqueta = f"desde el {_fmt(desde)}"
        else:
            etiqueta = f"hasta el {_fmt(hasta)}"
        return desde, hasta, etiqueta

    periodo = ALIAS_PERIODO.get(_norm(args.get("periodo")), defecto)
    if periodo == "ayer":
        ayer = hoy - timedelta(days=1)
        return ayer, ayer, f"ayer ({_fmt(ayer)})"
    if periodo == "semana":
        lunes = hoy - timedelta(days=hoy.weekday())
        return lunes, hoy, f"esta semana ({_fmt(lunes)} al {_fmt(hoy)})"
    if periodo == "mes":
        primero = hoy.replace(day=1)
        return primero, hoy, f"este mes ({_fmt(primero)} al {_fmt(hoy)})"
    if periodo == "mes_pasado":
        fin = hoy.replace(day=1) - timedelta(days=1)
        inicio = fin.replace(day=1)
        return inicio, fin, f"el mes pasado ({_fmt(inicio)} al {_fmt(fin)})"
    if periodo == "anio":
        inicio = hoy.replace(month=1, day=1)
        return inicio, hoy, f"este año ({_fmt(inicio)} al {_fmt(hoy)})"
    if periodo == "todo":
        return None, None, "todo el historial"
    return hoy, hoy, f"hoy ({_fmt(hoy)})"


def _estado(valor, catalogo):
    """Clave del estado (p. ej. 'EN_CAMINO') que corresponde al texto, o None."""
    if not _norm(valor):
        return None
    etiqueta = _resolver(valor, list(catalogo.values()))
    for clave, nombre in catalogo.items():
        if nombre == etiqueta:
            return clave
    return None


def _nombres_sucursales():
    """Nombres de las sucursales activas."""
    return list(
        Sucursal.objects.filter(estado="ACTIVA")
        .order_by("nombre")
        .values_list("nombre", flat=True)
    )


def alcance_sucursal(usuario):
    """Nombre de la única sucursal que el usuario puede consultar, o None.

    Hoy ningún usuario tiene una sucursal asignada (el modelo Usuario no la
    guarda) y el resto del sistema deja al encargado ver todas. Cuando se
    asigne una sucursal a cada encargado, solo hay que cambiar esta función.
    """
    return None


def _sucursal(args, usuario):
    """Devuelve (sucursal, nota): la sucursal a consultar y un aviso si aplica."""
    fija = alcance_sucursal(usuario)
    if fija:
        return fija, None
    valor = args.get("sucursal")
    if not _norm(valor):
        return None, None
    nombres = _nombres_sucursales()
    real = _resolver(valor, nombres)
    if real is None:
        return None, (
            f"No existe la sucursal «{valor}»; se muestran todas. "
            f"Sucursales: {', '.join(nombres)}."
        )
    return real, None


def _subtitulo(etiqueta, sucursal, extra=None):
    """Línea de contexto del resultado: periodo, sucursal y otros filtros."""
    partes = []
    if etiqueta:
        partes.append(f"Periodo: {etiqueta}")
    partes.append(f"Sucursal: {sucursal}" if sucursal else "Todas las sucursales")
    if extra:
        partes.extend(extra)
    return " · ".join(partes)


def _resultado(titulo, subtitulo, kpis, columnas, filas, notas=None):
    """Arma el resultado uniforme, recortando las filas al máximo permitido."""
    notas = list(notas or [])
    if len(filas) > MAX_FILAS:
        notas.append(
            f"Se muestran las primeras {MAX_FILAS} filas de {len(filas)}. "
            "Acota el periodo o la sucursal para ver el resto."
        )
        filas = filas[:MAX_FILAS]
    return {
        "titulo": titulo,
        "subtitulo": subtitulo,
        "kpis": kpis,
        "columnas": columnas,
        "filas": filas,
        "notas": notas,
    }


def _kpi(etiqueta, valor, tipo="numero"):
    """Un indicador destacado del resultado."""
    return {"etiqueta": etiqueta, "valor": valor, "tipo": tipo}


def _col(nombre, tipo="texto"):
    """Una columna de la tabla del resultado."""
    return {"nombre": nombre, "tipo": tipo}


def _fecha_local(momento):
    """Fecha (hora de Bolivia) de un datetime."""
    return timezone.localtime(momento).date()


# ---------------------------------------------------------------- inventario
def _cargar_stock(sucursal):
    """Una fila por variante y sucursal, con su cantidad y su mínimo."""
    stocks = StockItem.objects.filter(
        estado=True, id_variante__id_producto__estado="ACTIVO"
    ).select_related(
        "id_sucursal",
        "id_variante__id_producto__id_categoria",
        "id_variante__id_talla",
        "id_variante__id_color",
    )
    if sucursal:
        stocks = stocks.filter(id_sucursal__nombre=sucursal)
    filas = []
    for s in stocks:
        v = s.id_variante
        p = v.id_producto
        filas.append(
            {
                "prenda": p.nombre,
                "categoria": p.id_categoria.nombre,
                "talla": v.id_talla.nombre,
                "color": v.id_color.nombre,
                "sucursal": s.id_sucursal.nombre,
                "cantidad": s.cantidad,
                "minimo": s.stock_minimo,
                "tokens": set(
                    _tokens(
                        " ".join(
                            [
                                p.nombre,
                                p.tipo_prenda or "",
                                p.id_categoria.nombre,
                                v.id_color.nombre,
                                v.id_talla.nombre,
                            ]
                        )
                    )
                ),
            }
        )
    return filas


def _estado_stock(fila):
    """Agotado, Bajo (en o bajo su mínimo) u OK."""
    if fila["cantidad"] <= 0:
        return "Agotado"
    if fila["cantidad"] <= fila["minimo"]:
        return "Bajo"
    return "OK"


def _armar_inventario(filas, args, sucursal, notas):
    """Filtra y resume el stock según texto, categoría, talla, color y estado."""
    texto = _palabras_utiles(args.get("texto"))
    talla = _norm(args.get("talla"))
    color = args.get("color")
    categoria = args.get("categoria")
    solo_bajo = _verdadero(args.get("solo_bajo_stock"))

    elegidas = []
    for f in filas:
        if talla and _norm(f["talla"]) != talla:
            continue
        if _norm(color) and not _coincide(color, f["color"]):
            continue
        if _norm(categoria) and not _coincide(categoria, f["categoria"]):
            continue
        if solo_bajo and _estado_stock(f) == "OK":
            continue
        puntos = sum(1 for p in texto if p in f["tokens"]) if texto else 0
        if texto and puntos == 0:
            continue
        elegidas.append((puntos, f))
    if texto and elegidas:
        mejor = max(p for p, _ in elegidas)
        elegidas = [(p, f) for p, f in elegidas if p == mejor]

    elegidas = [f for _, f in elegidas]
    elegidas.sort(
        key=lambda f: (
            _norm(f["prenda"]),
            _norm(f["sucursal"]),
            _orden_talla(f["talla"]),
            _norm(f["color"]),
        )
    )
    filas_tabla = [
        [
            f["prenda"],
            f["categoria"],
            f["talla"],
            f["color"],
            f["sucursal"],
            f["cantidad"],
            f["minimo"],
            _estado_stock(f),
        ]
        for f in elegidas
    ]
    kpis = [
        _kpi("Unidades en stock", sum(f["cantidad"] for f in elegidas)),
        _kpi("Variantes listadas", len(elegidas)),
        _kpi("Con stock bajo", sum(1 for f in elegidas if _estado_stock(f) == "Bajo")),
        _kpi("Agotadas", sum(1 for f in elegidas if _estado_stock(f) == "Agotado")),
    ]
    extra = []
    if _norm(args.get("texto")):
        extra.append(f"Prenda: {args.get('texto')}")
    if solo_bajo:
        extra.append("Solo stock bajo")
    if not elegidas:
        notas = list(notas) + ["No hay variantes que coincidan con esos filtros."]
    return _resultado(
        "Inventario",
        _subtitulo(None, sucursal, extra),
        kpis,
        [
            _col("Prenda"),
            _col("Categoría"),
            _col("Talla"),
            _col("Color"),
            _col("Sucursal"),
            _col("Cantidad", "numero"),
            _col("Mínimo", "numero"),
            _col("Estado"),
        ],
        filas_tabla,
        notas,
    )


def consultar_inventario(args, usuario):
    """Stock por prenda y sucursal: cuánto queda, qué está bajo o agotado."""
    sucursal, nota = _sucursal(args, usuario)
    return _armar_inventario(_cargar_stock(sucursal), args, sucursal, [nota] if nota else [])


# ---------------------------------------------------------------- ventas
def _cargar_ventas(rango, sucursal, canal):
    """Ventas del periodo: punto de venta y órdenes web pagadas."""
    desde, hasta, _ = rango
    ventas = []
    if canal in (None, "pos"):
        qs = PosSale.objects.select_related("id_sucursal")
        if desde:
            qs = qs.filter(fecha_venta__date__gte=desde)
        if hasta:
            qs = qs.filter(fecha_venta__date__lte=hasta)
        if sucursal:
            qs = qs.filter(id_sucursal__nombre=sucursal)
        for v in qs:
            ventas.append(
                {
                    "canal": "Punto de venta",
                    "fecha": _fecha_local(v.fecha_venta),
                    "sucursal": v.id_sucursal.nombre,
                    "metodo": v.metodo_pago,
                    "total": _dinero(v.total),
                }
            )
    if canal in (None, "web"):
        qs = Order.objects.filter(estado__in=ESTADOS_PAGADOS).select_related("id_sucursal")
        if desde:
            qs = qs.filter(fecha_creacion__date__gte=desde)
        if hasta:
            qs = qs.filter(fecha_creacion__date__lte=hasta)
        if sucursal:
            qs = qs.filter(id_sucursal__nombre=sucursal)
        for o in qs:
            ventas.append(
                {
                    "canal": "Web / App",
                    "fecha": _fecha_local(o.fecha_creacion),
                    "sucursal": o.id_sucursal.nombre if o.id_sucursal else "Sin sucursal",
                    "metodo": o.metodo_pago,
                    "total": _dinero(o.total),
                }
            )
    return ventas


def _armar_ventas(ventas, args, etiqueta, sucursal, canal, notas):
    """Totales de ventas agrupados por día, sucursal, método de pago o canal."""
    agrupar = ALIAS_AGRUPAR.get(_norm(args.get("agrupar_por")), "dia")
    grupos = {}
    for v in ventas:
        clave = {
            "dia": v["fecha"],
            "sucursal": v["sucursal"],
            "metodo": v["metodo"],
            "canal": v["canal"],
        }[agrupar]
        acumulado = grupos.setdefault(clave, [0, 0.0])
        acumulado[0] += 1
        acumulado[1] += v["total"]

    if agrupar == "dia":
        orden = sorted(grupos.items(), key=lambda x: x[0])
        filas = [[_fmt(k), n, round(t, 2)] for k, (n, t) in orden]
    else:
        orden = sorted(grupos.items(), key=lambda x: -x[1][1])
        filas = [[k, n, round(t, 2)] for k, (n, t) in orden]

    total = round(sum(v["total"] for v in ventas), 2)
    cantidad = len(ventas)
    kpis = [
        _kpi("Total vendido", total, "dinero"),
        _kpi("Ventas realizadas", cantidad),
        _kpi("Ticket promedio", round(total / cantidad, 2) if cantidad else 0, "dinero"),
    ]
    if canal is None:
        for nombre in ("Punto de venta", "Web / App"):
            del_canal = [v for v in ventas if v["canal"] == nombre]
            kpis.append(
                _kpi(nombre, round(sum(v["total"] for v in del_canal), 2), "dinero")
            )
    extra = []
    if canal:
        extra.append("Canal: " + ("Punto de venta" if canal == "pos" else "Web / App"))
    extra.append(f"Agrupado por: {GRUPOS_VENTAS[agrupar].lower()}")
    if not ventas:
        notas = list(notas) + ["No hay ventas registradas en ese periodo."]
    return _resultado(
        "Ventas",
        _subtitulo(etiqueta, sucursal, extra),
        kpis,
        [_col(GRUPOS_VENTAS[agrupar]), _col("Ventas", "numero"), _col("Total (Bs)", "dinero")],
        filas,
        notas,
    )


def _canal(valor):
    """'pos' o 'web' según el texto, o None para ambos."""
    v = _norm(valor)
    if v in ("pos", "punto de venta", "presencial", "caja", "tienda"):
        return "pos"
    if v in ("web", "app", "online", "digital", "internet", "movil"):
        return "web"
    return None


def consultar_ventas(args, usuario):
    """Ventas por periodo, sucursal, canal y método de pago."""
    rango = _rango(args, "mes")
    sucursal, nota = _sucursal(args, usuario)
    canal = _canal(args.get("canal"))
    ventas = _cargar_ventas(rango, sucursal, canal)
    return _armar_ventas(ventas, args, rango[2], sucursal, canal, [nota] if nota else [])


# ---------------------------------------------------------------- entregas
def _cargar_entregas(rango, sucursal):
    """Entregas a domicilio del periodo, con su pedido y sucursal."""
    desde, hasta, _ = rango
    qs = Delivery.objects.select_related("id_orden__id_sucursal")
    if desde:
        qs = qs.filter(fecha_creacion__date__gte=desde)
    if hasta:
        qs = qs.filter(fecha_creacion__date__lte=hasta)
    if sucursal:
        qs = qs.filter(id_orden__id_sucursal__nombre=sucursal)
    filas = []
    for d in qs:
        orden = d.id_orden
        filas.append(
            {
                "pedido": d.id_orden_id,
                "fecha": _fecha_local(d.fecha_creacion),
                "estado": d.estado,
                "sucursal": orden.id_sucursal.nombre if orden.id_sucursal else "Sin sucursal",
                "distancia": float(d.distancia_km),
                "costo": _dinero(d.costo_envio),
            }
        )
    return filas


def _armar_entregas(filas, args, etiqueta, sucursal, notas):
    """Cantidad de entregas por estado y detalle de cada una."""
    estado = _estado(args.get("estado"), ESTADOS_ENTREGA)
    notas = list(notas)
    if _norm(args.get("estado")) and estado is None:
        notas.append(
            f"No existe el estado «{args.get('estado')}»; se muestran todos. "
            f"Estados: {', '.join(ESTADOS_ENTREGA.values())}."
        )
    elegidas = [f for f in filas if estado is None or f["estado"] == estado]
    elegidas.sort(key=lambda f: (f["fecha"], f["pedido"]), reverse=True)

    kpis = [_kpi("Entregas", len(elegidas))]
    for clave, nombre in KPI_ENTREGA.items():
        kpis.append(_kpi(nombre, sum(1 for f in elegidas if f["estado"] == clave)))
    kpis.append(_kpi("Costo de envíos", round(sum(f["costo"] for f in elegidas), 2), "dinero"))

    extra = [f"Estado: {ESTADOS_ENTREGA[estado]}"] if estado else []
    if not elegidas:
        notas.append("No hay entregas en ese periodo.")
    return _resultado(
        "Entregas a domicilio",
        _subtitulo(etiqueta, sucursal, extra),
        kpis,
        [
            _col("Pedido", "numero"),
            _col("Fecha"),
            _col("Estado"),
            _col("Sucursal"),
            _col("Distancia (km)", "numero"),
            _col("Costo envío (Bs)", "dinero"),
        ],
        [
            [
                f["pedido"],
                _fmt(f["fecha"]),
                ESTADOS_ENTREGA.get(f["estado"], f["estado"]),
                f["sucursal"],
                f["distancia"],
                f["costo"],
            ]
            for f in elegidas
        ],
        notas,
    )


def consultar_entregas(args, usuario):
    """Entregas a domicilio por periodo, estado y sucursal."""
    rango = _rango(args, "hoy")
    sucursal, nota = _sucursal(args, usuario)
    filas = _cargar_entregas(rango, sucursal)
    return _armar_entregas(filas, args, rango[2], sucursal, [nota] if nota else [])


# ---------------------------------------------------------------- reservas
def _cargar_reservas(rango, sucursal):
    """Reservas de prueba en tienda cuya fecha cae en el periodo."""
    desde, hasta, _ = rango
    qs = FittingReservation.objects.select_related("id_sucursal").prefetch_related("items")
    if desde:
        qs = qs.filter(fecha_reserva__gte=desde)
    if hasta:
        qs = qs.filter(fecha_reserva__lte=hasta)
    if sucursal:
        qs = qs.filter(id_sucursal__nombre=sucursal)
    return [
        {
            "reserva": r.id_reserva,
            "fecha": r.fecha_reserva,
            "hora": r.hora_reserva.strftime("%H:%M"),
            "sucursal": r.id_sucursal.nombre,
            "estado": r.estado,
            "prendas": len(r.items.all()),
        }
        for r in qs
    ]


def _armar_reservas(filas, args, etiqueta, sucursal, notas):
    """Cantidad de reservas por estado y detalle de cada una."""
    estado = _estado(args.get("estado"), ESTADOS_RESERVA)
    notas = list(notas)
    if _norm(args.get("estado")) and estado is None:
        notas.append(
            f"No existe el estado «{args.get('estado')}»; se muestran todos. "
            f"Estados: {', '.join(ESTADOS_RESERVA.values())}."
        )
    elegidas = [f for f in filas if estado is None or f["estado"] == estado]
    elegidas.sort(key=lambda f: (f["fecha"], f["hora"]))

    kpis = [_kpi("Reservas", len(elegidas))]
    for clave, nombre in ESTADOS_RESERVA.items():
        kpis.append(_kpi(nombre + "s", sum(1 for f in elegidas if f["estado"] == clave)))
    kpis.append(_kpi("Prendas reservadas", sum(f["prendas"] for f in elegidas)))

    extra = [f"Estado: {ESTADOS_RESERVA[estado]}"] if estado else []
    if not elegidas:
        notas.append("No hay reservas en ese periodo.")
    return _resultado(
        "Reservas de prueba en tienda",
        _subtitulo(etiqueta, sucursal, extra),
        kpis,
        [
            _col("Reserva", "numero"),
            _col("Fecha"),
            _col("Hora"),
            _col("Sucursal"),
            _col("Estado"),
            _col("Prendas", "numero"),
        ],
        [
            [
                f["reserva"],
                _fmt(f["fecha"]),
                f["hora"],
                f["sucursal"],
                ESTADOS_RESERVA.get(f["estado"], f["estado"]),
                f["prendas"],
            ]
            for f in elegidas
        ],
        notas,
    )


def consultar_reservas(args, usuario):
    """Reservas de prueba por periodo, estado y sucursal."""
    rango = _rango(args, "hoy")
    sucursal, nota = _sucursal(args, usuario)
    filas = _cargar_reservas(rango, sucursal)
    return _armar_reservas(filas, args, rango[2], sucursal, [nota] if nota else [])


# ---------------------------------------------------------------- más vendidos
def _cargar_items_vendidos(rango, sucursal):
    """Unidades y monto vendidos por prenda (punto de venta y web)."""
    desde, hasta, _ = rango
    filas = []

    web = OrderItem.objects.filter(id_orden__estado__in=ESTADOS_PAGADOS)
    if desde:
        web = web.filter(id_orden__fecha_creacion__date__gte=desde)
    if hasta:
        web = web.filter(id_orden__fecha_creacion__date__lte=hasta)
    if sucursal:
        web = web.filter(id_orden__id_sucursal__nombre=sucursal)

    pos = PosSaleItem.objects.all()
    if desde:
        pos = pos.filter(id_venta__fecha_venta__date__gte=desde)
    if hasta:
        pos = pos.filter(id_venta__fecha_venta__date__lte=hasta)
    if sucursal:
        pos = pos.filter(id_venta__id_sucursal__nombre=sucursal)

    for consulta in (web, pos):
        agregados = consulta.values("id_variante__id_producto__nombre").annotate(
            unidades=Sum("cantidad"), total=Sum("subtotal")
        )
        for r in agregados:
            filas.append(
                {
                    "prenda": r["id_variante__id_producto__nombre"],
                    "unidades": int(r["unidades"] or 0),
                    "total": _dinero(r["total"]),
                }
            )
    return filas


def _armar_mas_vendidos(filas, args, etiqueta, sucursal, notas):
    """Ranking de prendas por unidades vendidas."""
    limite = _entero(args.get("limite"), LIMITE_TOP, 1, MAX_TOP)
    por_prenda = {}
    for f in filas:
        acumulado = por_prenda.setdefault(f["prenda"], [0, 0.0])
        acumulado[0] += f["unidades"]
        acumulado[1] += f["total"]
    ranking = sorted(por_prenda.items(), key=lambda x: (-x[1][0], -x[1][1], x[0]))[:limite]

    kpis = [
        _kpi("Prendas distintas vendidas", len(por_prenda)),
        _kpi("Unidades vendidas", sum(u for u, _ in por_prenda.values())),
        _kpi("Total vendido", round(sum(t for _, t in por_prenda.values()), 2), "dinero"),
    ]
    if not ranking:
        notas = list(notas) + ["No hay ventas de prendas en ese periodo."]
    return _resultado(
        f"Prendas más vendidas (top {limite})",
        _subtitulo(etiqueta, sucursal),
        kpis,
        [_col("Puesto", "numero"), _col("Prenda"), _col("Unidades", "numero"), _col("Total (Bs)", "dinero")],
        [[i, nombre, u, round(t, 2)] for i, (nombre, (u, t)) in enumerate(ranking, start=1)],
        notas,
    )


def productos_mas_vendidos(args, usuario):
    """Ranking de prendas por unidades vendidas en un periodo."""
    rango = _rango(args, "mes")
    sucursal, nota = _sucursal(args, usuario)
    filas = _cargar_items_vendidos(rango, sucursal)
    return _armar_mas_vendidos(filas, args, rango[2], sucursal, [nota] if nota else [])


# ---------------------------------------------------------------- vestidor
def _cargar_pruebas(rango):
    """Pruebas en el vestidor virtual por prenda en el periodo."""
    desde, hasta, _ = rango
    qs = ARTryOnSession.objects.all()
    if desde:
        qs = qs.filter(fecha_sesion__date__gte=desde)
    if hasta:
        qs = qs.filter(fecha_sesion__date__lte=hasta)
    agregados = qs.values("id_producto__nombre").annotate(pruebas=Count("id_sesion"))
    return [
        {"prenda": r["id_producto__nombre"], "pruebas": int(r["pruebas"])}
        for r in agregados
    ]


def _armar_pruebas(filas, args, etiqueta, notas):
    """Prendas más probadas en el vestidor virtual."""
    limite = _entero(args.get("limite"), LIMITE_TOP, 1, MAX_TOP)
    ranking = sorted(filas, key=lambda f: (-f["pruebas"], f["prenda"]))[:limite]
    kpis = [
        _kpi("Pruebas realizadas", sum(f["pruebas"] for f in filas)),
        _kpi("Prendas probadas", len(filas)),
    ]
    if not ranking:
        notas = list(notas) + ["No hay pruebas en el vestidor virtual en ese periodo."]
    return _resultado(
        f"Uso del vestidor virtual (top {limite})",
        _subtitulo(etiqueta, None),
        kpis,
        [_col("Puesto", "numero"), _col("Prenda"), _col("Pruebas", "numero")],
        [[i, f["prenda"], f["pruebas"]] for i, f in enumerate(ranking, start=1)],
        notas,
    )


def uso_vestidor_virtual(args, usuario):
    """Prendas más probadas en el vestidor virtual (realidad aumentada)."""
    rango = _rango(args, "mes")
    return _armar_pruebas(_cargar_pruebas(rango), args, rango[2], [])


# ---------------------------------------------------------------- resumen
def resumen_general(args, usuario):
    """Indicadores clave del periodo: ventas, entregas, reservas, stock y pruebas."""
    rango = _rango(args, "hoy")
    sucursal, nota = _sucursal(args, usuario)
    ventas = _cargar_ventas(rango, sucursal, None)
    entregas = _cargar_entregas(rango, sucursal)
    reservas = _cargar_reservas(rango, sucursal)
    stock = _cargar_stock(sucursal)
    pruebas = _cargar_pruebas(rango)
    return _armar_resumen(
        ventas, entregas, reservas, stock, pruebas, rango[2], sucursal, [nota] if nota else []
    )


def _armar_resumen(ventas, entregas, reservas, stock, pruebas, etiqueta, sucursal, notas):
    """Junta los indicadores principales en una sola tabla."""
    total = round(sum(v["total"] for v in ventas), 2)
    bajo = sum(1 for f in stock if _estado_stock(f) == "Bajo")
    agotadas = sum(1 for f in stock if _estado_stock(f) == "Agotado")
    pendientes = sum(1 for f in entregas if f["estado"] != "ENTREGADO")
    filas = [
        ["Total vendido (Bs)", total],
        ["Ventas realizadas", len(ventas)],
        ["Entregas a domicilio", len(entregas)],
        ["Entregas sin completar", pendientes],
        ["Reservas de prueba", len(reservas)],
        ["Unidades en stock", sum(f["cantidad"] for f in stock)],
        ["Variantes con stock bajo", bajo],
        ["Variantes agotadas", agotadas],
        ["Pruebas en el vestidor virtual", sum(f["pruebas"] for f in pruebas)],
    ]
    kpis = [
        _kpi("Total vendido", total, "dinero"),
        _kpi("Entregas", len(entregas)),
        _kpi("Reservas", len(reservas)),
        _kpi("Stock bajo o agotado", bajo + agotadas),
    ]
    return _resultado(
        "Resumen general",
        _subtitulo(etiqueta, sucursal),
        kpis,
        [_col("Indicador"), _col("Valor", "numero")],
        filas,
        notas,
    )


# ---------------------------------------------------------------- definición
_PERIODO = {
    "type": "string",
    "description": "hoy, ayer, semana, mes, mes_pasado, anio o todo. Se ignora si das desde/hasta.",
}
_DESDE = {"type": "string", "description": "Fecha inicial AAAA-MM-DD (opcional)."}
_HASTA = {"type": "string", "description": "Fecha final AAAA-MM-DD (opcional)."}
_SUCURSAL = {
    "type": "string",
    "description": "Nombre (o parte) de la sucursal. Omítelo para todas.",
}

HERRAMIENTAS_ADMIN = [
    {
        "name": "consultar_inventario",
        "description": (
            "Stock por prenda y sucursal: cuánto queda, qué está bajo o agotado. Úsala "
            "para preguntas de inventario, existencias, 'cuánto me queda' o stock bajo."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "texto": {"type": "string", "description": "Nombre o tipo de prenda, ej. polera oversize."},
                "categoria": {"type": "string", "description": "Categoría de la prenda."},
                "talla": {"type": "string", "description": "Talla exacta, ej. M."},
                "color": {"type": "string", "description": "Un color, ej. negro."},
                "sucursal": _SUCURSAL,
                "solo_bajo_stock": {
                    "type": "boolean",
                    "description": "true para listar solo lo agotado o bajo su mínimo.",
                },
            },
        },
    },
    {
        "name": "consultar_ventas",
        "description": (
            "Ventas (punto de venta y web) por periodo. Total vendido, cantidad y ticket "
            "promedio, agrupados por día, sucursal, método de pago o canal."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "periodo": _PERIODO,
                "desde": _DESDE,
                "hasta": _HASTA,
                "sucursal": _SUCURSAL,
                "canal": {"type": "string", "description": "pos (punto de venta) o web. Omítelo para ambos."},
                "agrupar_por": {"type": "string", "description": "dia, sucursal, metodo o canal."},
            },
        },
    },
    {
        "name": "consultar_entregas",
        "description": (
            "Entregas a domicilio (delivery): cantidad por estado y detalle. Úsala para "
            "'cuántos envíos', entregas pendientes, en camino o entregadas."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "periodo": _PERIODO,
                "desde": _DESDE,
                "hasta": _HASTA,
                "estado": {
                    "type": "string",
                    "description": "pendiente, en preparación, en camino o entregado.",
                },
                "sucursal": _SUCURSAL,
            },
        },
    },
    {
        "name": "consultar_reservas",
        "description": (
            "Reservas de prueba de prendas en tienda: cantidad por estado y detalle."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "periodo": _PERIODO,
                "desde": _DESDE,
                "hasta": _HASTA,
                "estado": {
                    "type": "string",
                    "description": "pendiente, confirmada, completada o cancelada.",
                },
                "sucursal": _SUCURSAL,
            },
        },
    },
    {
        "name": "productos_mas_vendidos",
        "description": "Ranking de las prendas más vendidas (unidades y monto) en un periodo.",
        "parameters": {
            "type": "object",
            "properties": {
                "periodo": _PERIODO,
                "desde": _DESDE,
                "hasta": _HASTA,
                "sucursal": _SUCURSAL,
                "limite": {"type": "integer", "description": "Cuántas prendas mostrar (1 a 50)."},
            },
        },
    },
    {
        "name": "uso_vestidor_virtual",
        "description": "Prendas más probadas en el vestidor virtual (realidad aumentada).",
        "parameters": {
            "type": "object",
            "properties": {
                "periodo": _PERIODO,
                "desde": _DESDE,
                "hasta": _HASTA,
                "limite": {"type": "integer", "description": "Cuántas prendas mostrar (1 a 50)."},
            },
        },
    },
    {
        "name": "resumen_general",
        "description": (
            "Resumen de indicadores clave del periodo: ventas, entregas, reservas, stock "
            "bajo y pruebas en el vestidor. Úsala para preguntas generales del negocio."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "periodo": _PERIODO,
                "desde": _DESDE,
                "hasta": _HASTA,
                "sucursal": _SUCURSAL,
            },
        },
    },
]

CONSULTAS = {
    "consultar_inventario": consultar_inventario,
    "consultar_ventas": consultar_ventas,
    "consultar_entregas": consultar_entregas,
    "consultar_reservas": consultar_reservas,
    "productos_mas_vendidos": productos_mas_vendidos,
    "uso_vestidor_virtual": uso_vestidor_virtual,
    "resumen_general": resumen_general,
}


def ejecutar(nombre, argumentos, usuario):
    """Ejecuta una consulta de gestión y devuelve su resultado uniforme."""
    funcion = CONSULTAS.get(nombre)
    if funcion is None:
        raise ConsultaInvalida(f"Consulta desconocida: {nombre}")
    args = argumentos if isinstance(argumentos, dict) else {}
    return funcion(args, usuario)


def resumen_para_modelo(resultado, max_filas=12):
    """Versión compacta del resultado para que la IA redacte la respuesta."""
    columnas = [c["nombre"] for c in resultado["columnas"]]
    return {
        "titulo": resultado["titulo"],
        "subtitulo": resultado["subtitulo"],
        "indicadores": {k["etiqueta"]: k["valor"] for k in resultado["kpis"]},
        "total_filas": len(resultado["filas"]),
        "primeras_filas": [
            dict(zip(columnas, fila)) for fila in resultado["filas"][:max_filas]
        ],
        "notas": resultado["notas"],
    }