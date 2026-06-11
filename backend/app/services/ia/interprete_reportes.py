"""
interprete_reportes.py — Texto en lenguaje natural → QBE (Fase 2 de Reportes Dinámicos).

FLUJO:
  "Quiero los pagos de marzo agrupados por método"
        ↓  (este módulo, con Groq / Llama 3.3)
  { "entidad": "pagos", "rango_fechas": {...}, "group_by": ["metodo"], ... }
        ↓  (motor QBE ya existente: services/qbe_engine.py)
  Reporte con datos reales

SEGURIDAD: el LLM NUNCA genera SQL. Solo produce el JSON del QBE, que el
motor valida contra whitelists (entidades, campos, operadores cerrados).
Si el LLM "alucina" un campo, el motor responde 400 y este módulo le
reenvía el error para que se auto-corrija (un reintento).
"""
import json
import logging
from datetime import datetime

from app.config import settings
from app.schemas.reporte_qbe import QBERequest
from app.services.qbe_engine import describir_esquema

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Prompt del sistema
# ─────────────────────────────────────────────────────────────

# Valores reales de los enums de la BD — el LLM debe usar EXACTAMENTE estos
_VALORES_CONOCIDOS = """
Valores válidos para campos de estado (úsalos textualmente):
- asignaciones.estado: pendiente, buscando_taller, taller_asignado, en_camino, en_atencion, finalizado, cancelado, rechazada
- pagos.estado: pendiente, pagado
- pagos.metodo: efectivo, pasarela
- incidentes.estado: disponible, no_disponible
- mecanicos.estado: disponible, ocupado
"""

_EJEMPLOS = """
EJEMPLOS:

Usuario: "muéstrame los pagos pagados de este mes"
JSON:
{"entidad":"pagos","filtros":[{"campo":"estado","operador":"igual","valor":"pagado"}],"rango_fechas":{"desde":"{inicio_mes}T00:00:00","hasta":"{hoy}T23:59:59"},"orden":{"campo":"fecha_pago","direccion":"desc"}}

Usuario: "total de ingresos por método de pago del último trimestre"
JSON:
{"entidad":"pagos","filtros":[{"campo":"estado","operador":"igual","valor":"pagado"}],"rango_fechas":{"desde":"{hace_90}T00:00:00"},"group_by":["metodo"],"agregaciones":[{"funcion":"sumar","campo":"monto","alias":"ingresos"},{"funcion":"contar","alias":"cantidad"}],"orden":{"campo":"ingresos","direccion":"desc"}}

Usuario: "calificaciones con menos de 3 estrellas"
JSON:
{"entidad":"calificaciones","filtros":[{"campo":"puntuacion","operador":"menor_que","valor":3}],"orden":{"campo":"fecha","direccion":"desc"}}
"""


def _construir_system_prompt() -> str:
    """
    Arma el prompt del sistema inyectando el esquema REAL del motor QBE
    (entidades, campos, operadores) y la fecha actual para que el LLM
    resuelva expresiones como "este mes" o "la última semana".
    """
    esquema = describir_esquema()
    hoy = datetime.now()

    # Renderizar el esquema en texto compacto
    lineas_entidades = []
    for nombre, info in esquema["entidades"].items():
        fecha = f" (campo de fecha por defecto: {info['fecha_defecto']})" if info["fecha_defecto"] else ""
        lineas_entidades.append(f"- {nombre}: campos [{', '.join(info['campos'])}]{fecha}")

    ejemplos = (
        _EJEMPLOS
        .replace("{hoy}", hoy.strftime("%Y-%m-%d"))
        .replace("{inicio_mes}", hoy.strftime("%Y-%m-01"))
        .replace("{hace_90}", hoy.strftime("%Y-%m-%d"))  # el LLM ajusta solo
    )

    return f"""Eres un traductor de lenguaje natural a consultas QBE (Query by Example) en JSON para un sistema de auxilio vehicular en Bolivia. Respondes ÚNICAMENTE con un objeto JSON válido, sin explicaciones ni markdown.

FECHA ACTUAL: {hoy.strftime("%Y-%m-%d")} (úsala para resolver "hoy", "este mes", "último trimestre", etc.)

ESQUEMA DISPONIBLE (solo puedes usar estas entidades y campos):
{chr(10).join(lineas_entidades)}

OPERADORES de filtro: {', '.join(esquema['operadores'])}
FUNCIONES de agregación: {', '.join(esquema['agregaciones'])}
{_VALORES_CONOCIDOS}
ESTRUCTURA DEL JSON (omite las claves que no necesites):
{{"entidad":"...","filtros":[{{"campo":"...","operador":"...","valor":...}}],"rango_fechas":{{"campo":null,"desde":"YYYY-MM-DDTHH:MM:SS","hasta":"YYYY-MM-DDTHH:MM:SS"}},"group_by":["..."],"agregaciones":[{{"funcion":"...","campo":"...","alias":"..."}}],"orden":{{"campo":"...","direccion":"asc|desc"}},"pagina":1,"tamano_pagina":100}}

REGLAS:
1. Reporte de DETALLE (listar registros): NO uses group_by ni agregaciones.
2. Reporte AGRUPADO (totales, promedios, "por X"): usa group_by + al menos una agregación.
3. En rango_fechas, si no se indica campo usa null (el motor usa el de la entidad).
4. Las fechas siempre en formato ISO: YYYY-MM-DDTHH:MM:SS.
5. "incidencias"/"emergencias"/"solicitudes" = entidad incidentes. "servicios"/"trabajos" = entidad servicios.
6. Si piden datos de clientes que registraron incidentes, usa la entidad incidentes (tiene cliente_id); puedes agrupar por cliente_id.
7. Si el pedido es ambiguo, elige la interpretación más útil para un administrador de taller.
8. tamano_pagina máximo 1000. Por defecto usa 100.
{ejemplos}"""


# ─────────────────────────────────────────────────────────────
# Llamadas al LLM (Groq — Llama 3.3 70B, ya configurado en el proyecto)
# ─────────────────────────────────────────────────────────────

def _llamar_llm(mensajes: list[dict]) -> str:
    """Envía la conversación a Groq y devuelve el contenido (JSON en texto)."""
    if not settings.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY no está configurada en el .env — "
            "es necesaria para interpretar reportes en lenguaje natural."
        )
    from groq import Groq

    client = Groq(api_key=settings.GROQ_API_KEY)
    respuesta = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=mensajes,
        response_format={"type": "json_object"},  # fuerza JSON válido
        temperature=0.1,   # casi determinista: queremos precisión, no creatividad
        max_tokens=600,
    )
    return respuesta.choices[0].message.content.strip()


# ─────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────

def interpretar_prompt(texto: str) -> tuple[QBERequest, str]:
    """
    Traduce el prompt del usuario a un QBERequest validado.

    Retorna (qbe, modelo_usado).
    Lanza ValueError si el LLM no produce un QBE válido.
    """
    mensajes = [
        {"role": "system", "content": _construir_system_prompt()},
        {"role": "user", "content": texto},
    ]
    contenido = _llamar_llm(mensajes)
    logger.info(f"[IA Reportes] QBE generado: {contenido[:300]}")

    try:
        data = json.loads(contenido)
        qbe = QBERequest.model_validate(data)   # validación Pydantic estricta
    except Exception as e:
        raise ValueError(f"El LLM no produjo un QBE válido: {e}")

    return qbe, settings.GROQ_MODEL


def corregir_qbe(texto_original: str, qbe_fallido: QBERequest, error_motor: str) -> QBERequest:
    """
    Reintento de auto-corrección: le mostramos al LLM el QBE que generó
    y el error que devolvió el motor (que lista los campos/entidades
    válidos) para que produzca una versión corregida.
    """
    mensajes = [
        {"role": "system", "content": _construir_system_prompt()},
        {"role": "user", "content": texto_original},
        {"role": "assistant", "content": qbe_fallido.model_dump_json()},
        {
            "role": "user",
            "content": (
                f"El motor rechazó ese JSON con este error: \"{error_motor}\". "
                "Corrige el JSON usando SOLO entidades/campos válidos del esquema "
                "y responde únicamente con el JSON corregido."
            ),
        },
    ]
    contenido = _llamar_llm(mensajes)
    logger.info(f"[IA Reportes] QBE corregido: {contenido[:300]}")

    data = json.loads(contenido)
    return QBERequest.model_validate(data)
