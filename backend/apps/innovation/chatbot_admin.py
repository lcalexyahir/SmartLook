# backend/apps/innovation/chatbot_admin.py

import json
import logging

from django.utils import timezone

from . import consultas_admin as ca
from .chatbot import MensajeInvalido
from .llm import chat
from .models import ReporteAsistente

logger = logging.getLogger(__name__)

MAX_CARACTERES_MENSAJE = 500
MAX_CONSULTAS_POR_MENSAJE = 2
INTERCAMBIOS_PREVIOS = 3
TEMPERATURA_CONSULTA = 0.1
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MENSAJE_SIN_DATOS = (
    "No pude consultar esa información en este momento. "
    "Intenta de nuevo o reformula la pregunta."
)
MENSAJE_SIN_RESPUESTA = "No pude preparar una respuesta. ¿Puedes reformular tu pregunta?"

SIN_CONSULTA = {
    "name": "sin_consulta",
    "description": (
        "Úsala SOLO para saludos, agradecimientos, despedidas o temas que no tienen "
        "nada que ver con el negocio. NUNCA la uses si preguntan por inventario, "
        "stock, ventas, envíos, entregas, reservas, prendas vendidas o el vestidor "
        "virtual: para eso usa las demás herramientas."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "motivo": {
                "type": "string",
                "description": "saludo, agradecimiento, despedida u otro.",
            },
        },
    },
}
HERRAMIENTAS = ca.HERRAMIENTAS_ADMIN + [SIN_CONSULTA]


def _instrucciones():
    """Instrucciones del asistente con la fecha de hoy y las sucursales reales."""
    hoy = timezone.localdate()
    sucursales = ", ".join(ca._nombres_sucursales()) or "sin registrar"
    return (
        "Eres el asistente de gestión de SmartLook, una cadena de tiendas de ropa en "
        "Bolivia. Ayudas al personal (administradores y encargados) a consultar "
        "inventario, ventas, entregas, reservas y uso del vestidor virtual. Hablas en "
        "español, claro y breve.\n"
        f"Hoy es {DIAS[hoy.weekday()]} {hoy:%d/%m/%Y}. Los montos están en bolivianos (Bs).\n"
        "Reglas:\n"
        "- Para cualquier dato del negocio usa SIEMPRE una consulta. Nunca inventes "
        "cifras.\n"
        "- 'Cuánto me queda' o stock: consultar_inventario. 'Cuántos envíos': "
        "consultar_entregas. Ventas o ingresos: consultar_ventas. Lo que más se vende: "
        "productos_mas_vendidos. Preguntas generales del negocio: resumen_general.\n"
        "- Pasa solo lo que el usuario dijo. Si no menciona un periodo, no lo pases: "
        "cada consulta ya tiene uno por defecto. Las fechas relativas ('la semana "
        "pasada', 'del 1 al 15') conviértelas a desde/hasta con formato AAAA-MM-DD.\n"
        "- Después de la consulta responde en 2 o 3 frases con las cifras clave. La "
        "tabla completa se muestra aparte y se puede descargar en PDF, Excel y HTML.\n"
        "- Si el resultado trae 'notas', menciónalas.\n"
        "- No pidas ni menciones datos personales de clientes.\n"
        f"Sucursales: {sucursales}."
    )


def _instrucciones_respuesta(resumen=None):
    """Instrucciones para redactar la respuesta final, sin llamar herramientas.

    Se usan en la segunda llamada al modelo. No incluyen la regla de 'usa siempre
    una consulta': con ella el modelo intentaba llamar otra función y el
    proveedor rechazaba la petición.
    """
    base = (
        "Eres el asistente de gestión de SmartLook, una cadena de tiendas de ropa en "
        "Bolivia. Hablas en español, claro y breve. No llames a ninguna función ni "
        "herramienta: responde solo con texto. Los montos están en bolivianos (Bs). "
        "No pidas ni menciones datos personales de clientes.\n"
    )
    if resumen is None:
        return base + (
            "Responde al mensaje del usuario. Si pregunta por datos del negocio, "
            "pídele que lo formule como una pregunta concreta (inventario, ventas, "
            "entregas, reservas...)."
        )
    return base + (
        "Con estos resultados reales calculados por el sistema, responde al usuario en "
        "2 o 3 frases con las cifras clave, sin mencionar consultas, herramientas ni "
        "JSON. Si hay 'notas', menciónalas. La tabla completa se muestra aparte y se "
        "puede descargar en PDF, Excel y HTML:\n"
        + json.dumps(resumen, ensure_ascii=False)
    )


def _historial(usuario):
    """Últimas preguntas del usuario con su respuesta, de la más antigua a la nueva."""
    reportes = list(
        ReporteAsistente.objects.filter(id_usuario=usuario).order_by(
            "-fecha_creacion", "-id_reporte"
        )[:INTERCAMBIOS_PREVIOS]
    )
    mensajes = []
    for r in reversed(reportes):
        respuesta = (r.resultado or {}).get("respuesta") or r.titulo
        mensajes.append({"role": "user", "content": r.pregunta})
        mensajes.append({"role": "assistant", "content": respuesta[:600]})
    return mensajes


def _ejecutar_consultas(llamadas, usuario):
    """Ejecuta las consultas pedidas por el modelo (sin repetir ni pasarse).

    Devuelve (resultados, errores): resultados es una lista de
    (llamada, resultado); errores, los nombres de las consultas que fallaron.
    'sin_consulta' no consulta nada.
    """
    resultados, errores, vistas = [], [], set()
    for llamada in llamadas:
        if len(resultados) + len(errores) >= MAX_CONSULTAS_POR_MENSAJE:
            break
        if llamada["nombre"] == SIN_CONSULTA["name"]:
            continue
        clave = (llamada["nombre"], json.dumps(llamada["argumentos"], sort_keys=True))
        if clave in vistas:
            continue
        vistas.add(clave)
        try:
            resultado = ca.ejecutar(llamada["nombre"], llamada["argumentos"], usuario)
        except Exception:
            logger.exception("Falló la consulta de gestión %s", llamada["nombre"])
            errores.append(llamada["nombre"])
            continue
        resultados.append((llamada, resultado))
    return resultados, errores


def _guardar(usuario, mensaje, llamada, resultado, respuesta):
    """Guarda el resultado como reporte y devuelve el reporte creado."""
    return ReporteAsistente.objects.create(
        id_usuario=usuario,
        pregunta=mensaje,
        consulta=llamada["nombre"],
        filtros=llamada["argumentos"],
        titulo=resultado["titulo"][:200],
        resultado=dict(resultado, respuesta=respuesta),
    )


def responder_gestion(usuario, mensaje):
    """Responde una pregunta del personal y guarda los reportes generados.

    Devuelve {"respuesta", "resultados", "proveedor", "modelo"}. Cada elemento
    de "resultados" es {"id_reporte", "consulta", "resultado"}.
    """
    mensaje = (mensaje or "").strip()
    if not mensaje:
        raise MensajeInvalido("Escribe tu pregunta.")
    if len(mensaje) > MAX_CARACTERES_MENSAJE:
        raise MensajeInvalido(
            f"La pregunta no puede superar los {MAX_CARACTERES_MENSAJE} caracteres."
        )

    conversacion = (
        [{"role": "system", "content": _instrucciones()}]
        + _historial(usuario)
        + [{"role": "user", "content": mensaje}]
    )
    r = chat(
        conversacion,
        herramientas=HERRAMIENTAS,
        temperatura=TEMPERATURA_CONSULTA,
        forzar_herramienta=True,
    )

    resultados, errores = [], []
    if r["llamadas"]:
        resultados, errores = _ejecutar_consultas(r["llamadas"], usuario)
        if not resultados and errores:
            return {
                "respuesta": MENSAJE_SIN_DATOS,
                "resultados": [],
                "proveedor": r["proveedor"],
                "modelo": r["modelo"],
            }
        resumen = None
        if resultados:
            resumen = [
                {"consulta": ll["nombre"], **ca.resumen_para_modelo(res)}
                for ll, res in resultados
            ]
        r = chat(
            [
                {"role": "system", "content": _instrucciones_respuesta(resumen)},
                {"role": "user", "content": mensaje},
            ]
        )

    texto = r["texto"] or MENSAJE_SIN_RESPUESTA
    guardados = []
    for llamada, resultado in resultados:
        reporte = _guardar(usuario, mensaje, llamada, resultado, texto)
        guardados.append(
            {
                "id_reporte": reporte.id_reporte,
                "consulta": llamada["nombre"],
                "resultado": resultado,
            }
        )
    return {
        "respuesta": texto,
        "resultados": guardados,
        "proveedor": r["proveedor"],
        "modelo": r["modelo"],
    }