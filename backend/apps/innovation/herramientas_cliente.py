# backend/apps/innovation/herramientas_cliente.py
#
# NUEVO (CU18/CU19): herramientas que el asistente puede usar para responder
# al cliente con datos reales del sistema. El modelo elige la herramienta y sus
# filtros; los datos los calcula este módulo con el ORM, nunca el modelo.
#
# ejecutar(nombre, argumentos, cliente) devuelve (datos, tarjetas):
#   datos    -> resumen compacto (sin imágenes ni datos personales) que se le
#               entrega al modelo para redactar la respuesta.
#   tarjetas -> prendas con imagen para mostrarlas en la interfaz (CU18).
#
# La disponibilidad sale de StockItem (stock por sucursal), no de la variante.
#
# La búsqueda de prendas es tolerante a propósito: los modelos pequeños suelen
# poner palabras de relleno en los filtros ("colores", "talla") o confundir una
# marca con una talla. Por eso los valores se validan contra las tablas reales,
# lo desconocido se informa al modelo (no descarta todo) y, si no hay
# coincidencia exacta, se relajan algunos filtros avisando cuáles.

import logging
import re
import unicodedata
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from apps.catalog.models import (
    Categoria,
    Color,
    Marca,
    ProductoVariante,
    Sucursal,
    Talla,
    Temporada,
)
from apps.inventory.models import StockItem
from apps.sales.models import Order

logger = logging.getLogger(__name__)

LIMITE_DEFECTO = 6
LIMITE_MAXIMO = 8
MAX_OPCIONES_INFORMADAS = 15
ORDEN_TALLAS = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"]
GENEROS = {
    "hombre": "masculino",
    "hombres": "masculino",
    "varon": "masculino",
    "caballero": "masculino",
    "masculino": "masculino",
    "mujer": "femenino",
    "mujeres": "femenino",
    "dama": "femenino",
    "femenino": "femenino",
    "unisex": "unisex",
}
# Palabras que no describen una prenda y suelen colarse en el filtro de texto.
PALABRAS_RELLENO = {
    "que", "hay", "tienen", "tiene", "tienes", "tengan", "esta", "estan",
    "disponible", "disponibles", "stock", "color", "colores", "talla",
    "tallas", "precio", "precios", "cuesta", "cuestan", "cuanto", "quiero",
    "busco", "ropa", "prenda", "prendas", "modelo", "modelos", "sucursal",
    "sucursales", "para", "con", "sin", "una", "uno", "unos", "unas", "los",
    "las", "del", "por", "favor", "mas", "otro", "otra", "otros", "otras",
    "algo", "recomiendame", "recomienda", "recomiendas", "recomendable",
    "recomendacion", "recomendaciones", "recomendar", "sugiere", "sugieres",
    "sugerencia", "sugerencias", "necesito", "quisiera", "muestrame", "dame",
    "opcion", "opciones", "ver",
}
# Orden en que se sueltan filtros cuando no hay coincidencia exacta. El texto
# (qué prenda busca) va al final y solo se suelta si queda otro filtro activo,
# para no devolver medio catálogo por una búsqueda sin sentido.
ORDEN_RELAJACION = ("color", "talla", "temporada", "texto")


# ---------------------------------------------------------------- utilidades
def _norm(texto):
    """Devuelve el texto en minúsculas y sin tildes, para comparar."""
    t = unicodedata.normalize("NFD", str(texto or ""))
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower().strip()


def _base(palabra):
    """Reduce una palabra a su base: quita plural y la vocal final a/o.

    poleras -> poler, negra y negro -> negr, pantalones -> pantalon.
    """
    p = palabra
    if len(p) > 4 and p.endswith("es"):
        p = p[:-2]
    elif len(p) > 3 and p.endswith("s"):
        p = p[:-1]
    if len(p) > 3 and p[-1] in "ao":
        p = p[:-1]
    return p


def _tokens(texto):
    """Lista de palabras base de un texto (sin filtrar palabras de relleno)."""
    return [_base(p) for p in re.findall(r"[a-z0-9]+", _norm(texto))]


def _palabras_utiles(texto):
    """Palabras base de un texto libre, sin relleno y sin duplicados."""
    resultado = []
    for palabra in re.findall(r"[a-z0-9]+", _norm(texto)):
        if len(palabra) < 3 or palabra in PALABRAS_RELLENO:
            continue
        base = _base(palabra)
        if base not in resultado:
            resultado.append(base)
    return resultado


def _coincide(valor, opcion):
    """True si el valor del cliente corresponde a la opción del sistema.

    Compara por palabras base: 'azul' coincide con 'Azul Marino' y 'negra'
    con 'Negro'.
    """
    a, b = set(_tokens(valor)), set(_tokens(opcion))
    return bool(a) and bool(b) and (a <= b or b <= a)


def _resolver(valor, opciones, exacto=False):
    """Devuelve el nombre real de la opción que corresponde al valor, o None."""
    if not _norm(valor):
        return None
    for opcion in opciones:
        if exacto:
            if _norm(opcion) == _norm(valor):
                return opcion
        elif _coincide(valor, opcion):
            return opcion
    return None


def _entero(valor, defecto, minimo, maximo):
    """Convierte a entero y lo limita al rango [minimo, maximo]."""
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return defecto
    return max(minimo, min(maximo, n))


def _decimal(valor):
    """Convierte a Decimal, o None si no es un número."""
    if valor in (None, ""):
        return None
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError):
        return None


def _orden_talla(nombre):
    """Clave para ordenar tallas: XS, S, M, L, XL... y luego el resto."""
    n = str(nombre).upper()
    return (ORDEN_TALLAS.index(n) if n in ORDEN_TALLAS else 99, n)


def _temporadas_vigentes():
    """Ids de las temporadas cuyo rango de fechas incluye hoy."""
    hoy = timezone.localdate()
    return set(
        Temporada.objects.filter(
            estado=True, fecha_inicio__lte=hoy, fecha_fin__gte=hoy
        ).values_list("id_temporada", flat=True)
    )


# ---------------------------------------------------------------- catálogo
def _cargar_referencias():
    """Nombres reales de tallas, colores, marcas, etc., para validar filtros."""
    def nombres(modelo, campo="nombre"):
        return list(
            modelo.objects.filter(estado=True)
            .order_by(campo)
            .values_list(campo, flat=True)
        )

    return {
        "tallas": sorted(nombres(Talla), key=_orden_talla),
        "colores": nombres(Color),
        "marcas": nombres(Marca),
        "categorias": nombres(Categoria),
        "temporadas": nombres(Temporada),
        "sucursales": list(
            Sucursal.objects.filter(estado="ACTIVA")
            .order_by("nombre")
            .values_list("nombre", flat=True)
        ),
    }


def _cargar_catalogo():
    """Una fila por variante disponible con stock en alguna sucursal activa."""
    vigentes = _temporadas_vigentes()
    base = ProductoVariante.objects.filter(
        estado="DISPONIBLE", id_producto__estado="ACTIVO"
    )

    stock_por_variante = {}
    stocks = StockItem.objects.filter(
        estado=True,
        cantidad__gt=0,
        id_sucursal__estado="ACTIVA",
        id_variante__in=base.values("id_variante"),
    ).select_related("id_sucursal")
    for s in stocks:
        stock_por_variante.setdefault(s.id_variante_id, {})[
            s.id_sucursal.nombre
        ] = s.cantidad

    variantes = base.select_related(
        "id_producto__id_categoria",
        "id_producto__id_temporada",
        "id_producto__id_marca",
        "id_talla",
        "id_color",
    )
    filas = []
    for v in variantes:
        stock = stock_por_variante.get(v.id_variante)
        if not stock:
            continue
        p = v.id_producto
        marca = p.id_marca.nombre if p.id_marca else None
        temporada = p.id_temporada.nombre if p.id_temporada else None
        filas.append(
            {
                "id_producto": p.id_producto,
                "nombre": p.nombre,
                "categoria": p.id_categoria.nombre,
                "marca": marca,
                "temporada": temporada,
                "temporada_vigente": p.id_temporada_id in vigentes,
                "genero": p.genero,
                "imagen": p.imagen_producto,
                "talla": v.id_talla.nombre,
                "color": v.id_color.nombre,
                "precio": v.precio,
                "stock": stock,
                "tokens": set(
                    _tokens(
                        " ".join(
                            [
                                p.nombre,
                                p.tipo_prenda or "",
                                p.descripcion or "",
                                p.id_categoria.nombre,
                                marca or "",
                                v.id_color.nombre,
                                v.id_talla.nombre,
                            ]
                        )
                    )
                ),
            }
        )
    return filas


# ---------------------------------------------------------------- búsqueda
def _normalizar_filtros(args, ref):
    """Valida los filtros del modelo contra las tablas reales.

    Devuelve (filtros, no_reconocidos). Un valor que no existe (por ejemplo la
    marca 'BTS') no se aplica: se anota en no_reconocidos con las opciones
    reales para que el asistente se lo explique al cliente.
    """
    no_reconocidos = []

    def resolver(clave, opciones, exacto=False):
        valor = args.get(clave)
        if not _norm(valor):
            return None
        real = _resolver(valor, opciones, exacto)
        if real is None:
            no_reconocidos.append(
                {
                    "filtro": clave,
                    "valor": str(valor),
                    "opciones_validas": opciones[:MAX_OPCIONES_INFORMADAS],
                }
            )
        return real

    texto = _palabras_utiles(args.get("texto"))
    categoria = None
    if _norm(args.get("categoria")):
        categoria = _resolver(args.get("categoria"), ref["categorias"])
        # Lo que sobra de la categoría (p. ej. "Polera Oversize" -> "oversize",
        # o una categoría inexistente) se trata como texto libre.
        conocidas = set(_tokens(categoria)) if categoria else set()
        for palabra in _palabras_utiles(args.get("categoria")):
            if palabra not in conocidas and palabra not in texto:
                texto.append(palabra)

    genero = GENEROS.get(_norm(args.get("genero")))
    filtros = {
        "texto": texto,
        "categoria": categoria,
        "marca": resolver("marca", ref["marcas"]),
        "temporada": resolver("temporada", ref["temporadas"]),
        "talla": resolver("talla", ref["tallas"], exacto=True),
        "color": resolver("color", ref["colores"]),
        "sucursal": resolver("sucursal", ref["sucursales"]),
        "genero": genero,
        "precio_max": _decimal(args.get("precio_max")),
    }
    return filtros, no_reconocidos


def _seleccionar(filas, f):
    """Aplica los filtros a las filas y devuelve los productos ordenados.

    Los filtros validados (talla, color, marca...) son estrictos. El texto libre
    puntúa: basta una palabra que coincida y gana quien más coincide.
    """
    productos = {}
    for r in filas:
        stock = r["stock"]
        if f["sucursal"]:
            stock = {n: c for n, c in stock.items() if _norm(n) == _norm(f["sucursal"])}
            if not stock:
                continue
        if f["talla"] and _norm(r["talla"]) != _norm(f["talla"]):
            continue
        if f["color"] and _norm(r["color"]) != _norm(f["color"]):
            continue
        if f["marca"] and _norm(r["marca"]) != _norm(f["marca"]):
            continue
        if f["categoria"] and _norm(r["categoria"]) != _norm(f["categoria"]):
            continue
        if f["temporada"] and _norm(r["temporada"]) != _norm(f["temporada"]):
            continue
        if f["genero"] and _norm(r["genero"]) not in (f["genero"], "unisex"):
            continue
        if f["precio_max"] is not None and r["precio"] > f["precio_max"]:
            continue
        puntos = 0
        if f["texto"]:
            puntos = sum(1 for palabra in f["texto"] if palabra in r["tokens"])
            if puntos == 0:
                continue

        d = productos.setdefault(
            r["id_producto"],
            {"r": r, "precios": [], "tallas": set(), "colores": set(),
             "stock": {}, "puntos": 0},
        )
        d["puntos"] = max(d["puntos"], puntos)
        d["precios"].append(r["precio"])
        d["tallas"].add(r["talla"])
        d["colores"].add(r["color"])
        for nombre, cantidad in stock.items():
            d["stock"][nombre] = d["stock"].get(nombre, 0) + cantidad

    lista = list(productos.values())
    if f["texto"] and lista:
        mejor = max(d["puntos"] for d in lista)
        lista = [d for d in lista if d["puntos"] == mejor]
    return sorted(
        lista,
        key=lambda d: (
            -d["puntos"],
            0 if d["r"]["temporada_vigente"] else 1,
            _norm(d["r"]["nombre"]),
        ),
    )


def _hay_otros_filtros(filtros):
    """True si, además del texto, hay algún otro filtro activo."""
    claves = ("categoria", "marca", "temporada", "talla", "color", "sucursal", "genero")
    return any(filtros.get(k) for k in claves) or filtros.get("precio_max") is not None


def _buscar_prendas(args):
    """Herramienta buscar_prendas: prendas con stock, con filtros tolerantes."""
    limite = _entero(args.get("limite"), LIMITE_DEFECTO, 1, LIMITE_MAXIMO)
    ref = _cargar_referencias()
    filas = _cargar_catalogo()
    filtros, no_reconocidos = _normalizar_filtros(args, ref)

    seleccion = _seleccionar(filas, filtros)
    ignorados = []
    for nombre in ORDEN_RELAJACION:
        if seleccion:
            break
        valor = filtros.get(nombre)
        if not valor:
            continue
        if nombre == "texto" and not _hay_otros_filtros(filtros):
            break
        etiqueta = args.get(nombre) or (
            " ".join(valor) if isinstance(valor, list) else valor
        )
        ignorados.append(f"{nombre}: {etiqueta}")
        filtros = {**filtros, nombre: [] if nombre == "texto" else None}
        seleccion = _seleccionar(filas, filtros)

    prendas, tarjetas = [], []
    for d in seleccion[:limite]:
        r = d["r"]
        tallas = sorted(d["tallas"], key=_orden_talla)
        colores = sorted(d["colores"])
        sucursales = [
            f"{nombre} ({unidades} u.)"
            for nombre, unidades in sorted(d["stock"].items(), key=lambda x: -x[1])[:4]
        ]
        desde, hasta = float(min(d["precios"])), float(max(d["precios"]))
        prendas.append(
            {
                "id": r["id_producto"],
                "nombre": r["nombre"],
                "categoria": r["categoria"],
                "marca": r["marca"],
                "temporada": r["temporada"],
                "temporada_vigente": r["temporada_vigente"],
                "genero": r["genero"],
                "precio_desde_bs": desde,
                "precio_hasta_bs": hasta,
                "tallas": tallas,
                "colores": colores,
                "sucursales_con_stock": sucursales,
            }
        )
        tarjetas.append(
            {
                "id_producto": r["id_producto"],
                "nombre": r["nombre"],
                "categoria": r["categoria"],
                "temporada": r["temporada"],
                "precio_desde": desde,
                "precio_hasta": hasta,
                "tallas": tallas,
                "colores": colores,
                "sucursales": sucursales,
                "imagen": r["imagen"],
            }
        )

    datos = {
        "total_encontradas": len(seleccion),
        "mostrando": len(prendas),
        "prendas": prendas,
    }
    if no_reconocidos:
        datos["no_reconocidos"] = no_reconocidos
    if ignorados and prendas:
        datos["filtros_ignorados"] = ignorados
    if not prendas:
        datos["nota"] = "No hay prendas disponibles con esos filtros."
    return datos, tarjetas


def _ver_sucursales(args):
    """Herramienta ver_sucursales: sucursales activas con su horario."""
    f_ciudad = _norm(args.get("ciudad"))
    filas = []
    sucursales = (
        Sucursal.objects.filter(estado="ACTIVA")
        .select_related("id_ciudad")
        .order_by("nombre")
    )
    for s in sucursales:
        if f_ciudad and f_ciudad not in _norm(s.id_ciudad.nombre):
            continue
        filas.append(
            {
                "nombre": s.nombre,
                "ciudad": s.id_ciudad.nombre,
                "direccion": s.direccion,
                "telefono": s.telefono or "no registrado",
                "dias_atencion": s.dias_atencion or "no registrado",
                "horario_atencion": s.horario_atencion or "no registrado",
            }
        )
    datos = {"sucursales": filas}
    if not filas:
        datos["nota"] = "No hay sucursales activas con ese filtro."
    return datos, []


def _mis_pedidos(args, cliente):
    """Herramienta mis_pedidos: pedidos recientes del cliente autenticado."""
    if cliente is None:
        return {"error": "Debes iniciar sesión para consultar tus pedidos."}, []
    limite = _entero(args.get("limite"), 5, 1, 10)
    pedidos = (
        Order.objects.filter(id_cliente=cliente)
        .select_related("id_sucursal", "delivery")
        .order_by("-fecha_creacion")[:limite]
    )
    filas = []
    for o in pedidos:
        entrega = getattr(o, "delivery", None)
        filas.append(
            {
                "numero": o.id_orden,
                "fecha": timezone.localtime(o.fecha_creacion).strftime("%d/%m/%Y %H:%M"),
                "estado": o.estado,
                "tipo_entrega": o.tipo_entrega,
                "total_bs": float(o.total),
                "sucursal": o.id_sucursal.nombre if o.id_sucursal else None,
                "estado_entrega": entrega.estado if entrega else None,
            }
        )
    datos = {"pedidos": filas}
    if not filas:
        datos["nota"] = "El cliente todavía no tiene pedidos."
    return datos, []


# ---------------------------------------------------------------- definición
HERRAMIENTAS_CLIENTE = [
    {
        "name": "buscar_prendas",
        "description": (
            "Busca prendas disponibles (con stock) en el catálogo y devuelve precios, "
            "tallas, colores y las sucursales donde hay stock. Úsala para recomendar, "
            "comparar o consultar disponibilidad. Todos los filtros son opcionales: "
            "pasa solo lo que el cliente dijo y nunca pongas palabras como 'talla' o "
            "'colores' como valor de un filtro. Si el cliente pregunta qué colores o "
            "tallas hay de una prenda, busca la prenda solo con 'texto'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "texto": {
                    "type": "string",
                    "description": "Nombre o tipo de prenda, por ejemplo: polera oversize, jean, chaqueta.",
                },
                "categoria": {"type": "string", "description": "Nombre de la categoría."},
                "marca": {
                    "type": "string",
                    "description": "Marca de la prenda (no es una talla).",
                },
                "temporada": {
                    "type": "string",
                    "description": "Temporada, por ejemplo: verano, invierno, nueva colección.",
                },
                "genero": {
                    "type": "string",
                    "description": "MASCULINO, FEMENINO o UNISEX.",
                },
                "talla": {"type": "string", "description": "Talla exacta, por ejemplo: M."},
                "color": {"type": "string", "description": "Un color, por ejemplo: negro."},
                "sucursal": {
                    "type": "string",
                    "description": "Nombre (o parte) de la sucursal donde debe haber stock.",
                },
                "precio_max": {
                    "type": "number",
                    "description": "Precio máximo en bolivianos (Bs).",
                },
                "limite": {
                    "type": "integer",
                    "description": "Cantidad máxima de prendas a mostrar (1 a 8).",
                },
            },
        },
    },
    {
        "name": "ver_sucursales",
        "description": (
            "Lista las sucursales activas con ciudad, dirección, teléfono, días y "
            "horario de atención."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ciudad": {"type": "string", "description": "Filtrar por ciudad."},
            },
        },
    },
    {
        "name": "mis_pedidos",
        "description": (
            "Muestra los pedidos más recientes del cliente que escribe, con su estado "
            "y el estado de la entrega a domicilio si la tiene."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limite": {
                    "type": "integer",
                    "description": "Cantidad de pedidos a mostrar (1 a 10).",
                },
            },
        },
    },
]


def ejecutar(nombre, argumentos, cliente=None):
    """Ejecuta una herramienta. Devuelve (datos_para_el_modelo, tarjetas)."""
    args = argumentos if isinstance(argumentos, dict) else {}
    try:
        if nombre == "buscar_prendas":
            return _buscar_prendas(args)
        if nombre == "ver_sucursales":
            return _ver_sucursales(args)
        if nombre == "mis_pedidos":
            return _mis_pedidos(args, cliente)
    except Exception:
        logger.exception("Falló la herramienta %s", nombre)
        return {"error": "No se pudo consultar la información en este momento."}, []
    return {"error": f"Herramienta desconocida: {nombre}"}, []


# ---------------------------------------------------------------- instrucciones
def prompt_sistema_cliente():
    """Instrucciones del asistente para clientes, con datos vigentes del sistema."""
    hoy = timezone.localdate()
    ref = _cargar_referencias()
    vigentes = ", ".join(
        Temporada.objects.filter(
            estado=True, fecha_inicio__lte=hoy, fecha_fin__gte=hoy
        ).values_list("nombre", flat=True)
    )
    return (
        "Eres el asistente virtual de SmartLook, una cadena de tiendas de ropa en "
        "Bolivia. Hablas en español, con tono cercano y breve (máximo 5 frases; "
        "listas cortas si ayudan).\n"
        f"Hoy es {hoy:%d/%m/%Y}. Los precios están en bolivianos (Bs).\n"
        "Reglas:\n"
        "- Para hablar de prendas, precios, tallas, colores, stock, sucursales u "
        "horarios usa SIEMPRE las herramientas. Nunca inventes datos.\n"
        "- A las herramientas pásales solo lo que el cliente dijo. Una marca va en "
        "'marca', nunca como talla. Si pregunta qué colores o tallas hay de una "
        "prenda, busca la prenda solo por su nombre y responde con los colores y "
        "tallas del resultado.\n"
        "- Si el resultado trae 'no_reconocidos', di primero que ese dato no existe "
        "en la tienda (por ejemplo, que no manejamos esa marca) y ofrece lo que sí "
        "hay usando 'opciones_validas'.\n"
        "- Si el resultado trae 'filtros_ignorados', avisa que no hubo coincidencia "
        "exacta con esos datos y que estas son las opciones más cercanas.\n"
        "- Si el resultado trae prendas, nunca digas que no hay disponibles. Si no "
        "trae ninguna, dilo y sugiere cambiar un filtro.\n"
        "- Para recomendar, prefiere las prendas de la temporada vigente y ofrece "
        "2 o 3 opciones con nombre, precio y sucursales con stock.\n"
        "- Solo respondes sobre la tienda, sus prendas, sucursales y los pedidos "
        "del propio cliente. Si preguntan otra cosa, indícalo con amabilidad.\n"
        "- No pidas ni menciones datos personales.\n"
        "- Las reservas y las compras se hacen desde la app o la web; tú no las "
        "ejecutas.\n"
        f"Categorías: {', '.join(ref['categorias']) or 'sin registrar'}.\n"
        f"Marcas: {', '.join(ref['marcas']) or 'sin registrar'}.\n"
        f"Tallas: {', '.join(ref['tallas']) or 'sin registrar'}.\n"
        f"Temporadas: {', '.join(ref['temporadas']) or 'sin registrar'}.\n"
        f"Temporadas vigentes hoy: {vigentes or 'ninguna registrada'}."
    )