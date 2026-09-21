# backend/apps/innovation/chatbot.py
#
# NUEVO (CU18/CU19): lógica del asistente virtual para clientes.
#
# Flujo de cada mensaje:
#   1. Se arma la conversación: instrucciones + últimos intercambios + mensaje.
#   2. El modelo está OBLIGADO a elegir una consulta: buscar prendas, ver
#      sucursales, ver pedidos, o "sin_consulta" (saludos, agradecimientos o
#      temas ajenos a la tienda). Así no puede contestar de memoria sobre
#      prendas, stock o precios.
#   3. Las consultas las ejecuta el código (herramientas_cliente.py) con el
#      cliente autenticado; el modelo nunca elige de quién son los datos.
#   4. Con los datos reales se pide la respuesta final y se guarda el
#      intercambio en ChatbotConversation.
#
# Devuelve el texto y las tarjetas de prendas para mostrarlas en la interfaz.
# Si ningún proveedor de IA responde, lanza ServicioIANoDisponible.

import json
import logging

from apps.catalog.models import Producto

from . import herramientas_cliente as hc
from .llm import chat
from .models import ChatbotConversation

logger = logging.getLogger(__name__)

MAX_CARACTERES_MENSAJE = 500
INTERCAMBIOS_PREVIOS = 4
MAX_CONSULTAS_POR_MENSAJE = 3
TEMPERATURA_CONSULTA = 0.1
MENSAJE_SIN_RESPUESTA = "No pude preparar una respuesta. ¿Puedes reformular tu consulta?"

SIN_CONSULTA = {
    "name": "sin_consulta",
    "description": (
        "Úsala SOLO para saludos, agradecimientos, despedidas o temas que no tienen "
        "nada que ver con la tienda. NUNCA la uses si el cliente pregunta por "
        "prendas, ropa, precios, tallas, colores, marcas, stock, disponibilidad, "
        "sucursales, horarios o pedidos: para eso usa las demás herramientas."
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
HERRAMIENTAS = hc.HERRAMIENTAS_CLIENTE + [SIN_CONSULTA]


class MensajeInvalido(Exception):
    """El mensaje del cliente está vacío o es demasiado largo."""


def _generos_con_prendas():
    """Géneros que tienen productos activos en el catálogo, ej. 'MASCULINO'."""
    generos = (
        Producto.objects.filter(estado="ACTIVO")
        .values_list("genero", flat=True)
        .distinct()
    )
    return ", ".join(sorted({g for g in generos if g})) or "sin registrar"


def _instrucciones():
    """Instrucciones base del asistente más las reglas sobre géneros y consultas."""
    return (
        hc.prompt_sistema_cliente()
        + f"\nGéneros con prendas en el catálogo: {_generos_con_prendas()}.\n"
        "- Solo existen prendas para los géneros indicados arriba. Si preguntan por "
        "otro (por ejemplo, ropa femenina) y no está en esa lista, di con "
        "amabilidad que por ahora no manejas ese tipo de ropa y ofrece lo que sí hay.\n"
        "- Nunca respondas de memoria sobre prendas, precios, tallas, stock, "
        "sucursales u horarios: usa siempre una consulta."
    )


def _historial(cliente):
    """Últimos intercambios del cliente, del más antiguo al más nuevo."""
    filas = list(
        ChatbotConversation.objects.filter(id_cliente=cliente).order_by(
            "-fecha_mensaje", "-id_conversacion"
        )[:INTERCAMBIOS_PREVIOS]
    )
    mensajes = []
    for f in reversed(filas):
        mensajes.append({"role": "user", "content": f.mensaje_usuario})
        mensajes.append({"role": "assistant", "content": f.respuesta_bot[:600]})
    return mensajes


def _ejecutar_consultas(llamadas, cliente):
    """Ejecuta las consultas pedidas por el modelo (sin repetir ni pasarse).

    Devuelve (resultados, tarjetas). 'sin_consulta' no consulta nada.
    """
    resultados, tarjetas, vistas = [], [], set()
    for llamada in llamadas[:MAX_CONSULTAS_POR_MENSAJE]:
        if llamada["nombre"] == SIN_CONSULTA["name"]:
            continue
        clave = (llamada["nombre"], json.dumps(llamada["argumentos"], sort_keys=True))
        if clave in vistas:
            continue
        vistas.add(clave)
        datos, cards = hc.ejecutar(llamada["nombre"], llamada["argumentos"], cliente)
        resultados.append(
            {
                "consulta": llamada["nombre"],
                "filtros": llamada["argumentos"],
                "resultado": datos,
            }
        )
        tarjetas.extend(cards)
    return resultados, tarjetas


def responder_cliente(cliente, mensaje):
    """Responde el mensaje del cliente y guarda el intercambio."""
    mensaje = (mensaje or "").strip()
    if not mensaje:
        raise MensajeInvalido("Escribe tu consulta.")
    if len(mensaje) > MAX_CARACTERES_MENSAJE:
        raise MensajeInvalido(
            f"El mensaje no puede superar los {MAX_CARACTERES_MENSAJE} caracteres."
        )

    conversacion = (
        [{"role": "system", "content": _instrucciones()}]
        + _historial(cliente)
        + [{"role": "user", "content": mensaje}]
    )

    r = chat(
        conversacion,
        herramientas=HERRAMIENTAS,
        temperatura=TEMPERATURA_CONSULTA,
        forzar_herramienta=True,
    )

    tarjetas = []
    if r["llamadas"]:
        resultados, tarjetas = _ejecutar_consultas(r["llamadas"], cliente)
        if resultados:
            conversacion.append(
                {
                    "role": "system",
                    "content": (
                        "Resultados reales de las consultas al sistema. Responde al "
                        "cliente usando solo estos datos, sin mencionar consultas, "
                        "herramientas ni JSON:\n"
                        + json.dumps(resultados, ensure_ascii=False)
                    ),
                }
            )
        r = chat(conversacion)

    texto = r["texto"] or MENSAJE_SIN_RESPUESTA

    # Una tarjeta por producto; si el texto nombra algunas, se muestran solo esas.
    unicas = {}
    for t in tarjetas:
        unicas.setdefault(t["id_producto"], t)
    tarjetas = list(unicas.values())
    texto_norm = hc._norm(texto)
    mencionadas = [t for t in tarjetas if hc._norm(t["nombre"]) in texto_norm]
    if mencionadas:
        tarjetas = mencionadas

    ChatbotConversation.objects.create(
        id_cliente=cliente, mensaje_usuario=mensaje, respuesta_bot=texto
    )
    return {
        "respuesta": texto,
        "tarjetas": tarjetas,
        "proveedor": r["proveedor"],
        "modelo": r["modelo"],
    }