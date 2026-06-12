"""
generador_resumen.py — Ficha estructurada del incidente con LLM local.

MODELO: Gemma 2 2B (cuantizado, ~1.7 GB) ejecutado por OLLAMA.

¿POR QUÉ OLLAMA?
  Ollama es un programa aparte que gestiona los modelos de lenguaje:
  los descarga, los carga/descarga de memoria solo cuando se usan, y
  expone una API HTTP en http://localhost:11434. Así el backend Python
  NO carga el LLM en su propio proceso (clave con 8 GB de RAM).

ESTRATEGIA DE DOBLE NIVEL (siempre funciona):
  1. Si Ollama está corriendo  → genera la ficha con Gemma 2B (texto natural).
  2. Si Ollama NO está corriendo → genera la ficha con una PLANTILLA
     estructurada (sin IA). El endpoint nunca falla por falta de hardware.

INSTALACIÓN DE OLLAMA (ver MODULO-IA.md):
  1. Descargar de https://ollama.com/download/windows
  2. En una terminal:  ollama pull gemma2:2b     (descarga ~1.6 GB)
  3. Listo: Ollama queda como servicio en localhost:11434
"""
import logging
from datetime import datetime

import requests

from app.config import settings

logger = logging.getLogger(__name__)

# URL y modelo de Ollama (configurables desde .env)
OLLAMA_URL = getattr(settings, "OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODELO = getattr(settings, "OLLAMA_MODELO", "gemma2:2b")

# Tiempo máximo de espera para la generación (Gemma 2B en CPU tarda
# entre 15 y 60 segundos según la carga de la máquina)
TIMEOUT_GENERACION = 90


# ─────────────────────────────────────────────────────────────
# Disponibilidad de Ollama
# ─────────────────────────────────────────────────────────────

def ollama_disponible() -> bool:
    """True si el servicio Ollama responde en localhost:11434."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except requests.RequestException:
        return False


def modelo_descargado() -> bool:
    """True si el modelo (gemma2:2b) ya fue descargado en Ollama."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        modelos = [m.get("name", "") for m in r.json().get("models", [])]
        return any(OLLAMA_MODELO in m for m in modelos)
    except requests.RequestException:
        return False


# ─────────────────────────────────────────────────────────────
# Construcción del contexto del incidente
# ─────────────────────────────────────────────────────────────

def _contexto_incidente(incidente) -> dict:
    """Extrae los datos relevantes del incidente para armar la ficha."""
    cliente = incidente.cliente.usuario if incidente.cliente and incidente.cliente.usuario else None
    vehiculo = incidente.vehiculo
    categoria = incidente.categoria

    fotos = sum(1 for e in incidente.evidencias if e.tipo.value == "foto")
    audios = sum(1 for e in incidente.evidencias if e.tipo.value == "audio")

    return {
        "id": incidente.id,
        "descripcion": incidente.descripcion,
        "fecha": incidente.fecha_hora.strftime("%d/%m/%Y %H:%M"),
        "categoria": categoria.nombre if categoria else "Sin categoría",
        "prioridad": categoria.prioridad if categoria else 1,
        "cliente": f"{cliente.nombre} {cliente.apellido}" if cliente else "Desconocido",
        "vehiculo": f"{vehiculo.modelo} {vehiculo.color} (placa {vehiculo.placa})" if vehiculo else "No registrado",
        "ubicacion": f"lat {incidente.latitud}, lng {incidente.longitud}",
        "evidencias": f"{fotos} foto(s), {audios} audio(s)",
    }


# ─────────────────────────────────────────────────────────────
# Nivel 1 — Generación con Gemma 2B (Ollama)
# ─────────────────────────────────────────────────────────────

def _generar_con_ollama(ctx: dict) -> str:
    """
    Pide a Gemma 2B (vía Ollama) que redacte la ficha del incidente.
    Lanza excepción si Ollama no responde (el caller hace el fallback).
    """
    prompt = f"""Eres un asistente de una plataforma de auxilio vehicular en Bolivia.
Redacta una FICHA DE INCIDENTE breve y profesional en español, usando EXACTAMENTE este formato:

RESUMEN: (2-3 frases describiendo el problema y su contexto)
TIPO DE PROBLEMA: (una categoría: batería / llanta / choque / motor / otro)
NIVEL DE URGENCIA: (Alta, Media o Baja, con justificación de una frase)
RECOMENDACIÓN AL TALLER: (qué herramientas/repuestos llevar, en 1-2 frases)

Datos del incidente:
- Descripción del cliente: "{ctx['descripcion']}"
- Categoría reportada: {ctx['categoria']}
- Vehículo: {ctx['vehiculo']}
- Fecha y hora: {ctx['fecha']}
- Evidencias adjuntas: {ctx['evidencias']}

No inventes datos que no tengas. Responde SOLO con la ficha, sin saludos."""

    respuesta = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODELO,
            "prompt": prompt,
            "stream": False,           # respuesta completa de una vez
            "options": {
                "temperature": 0.3,    # baja temperatura = respuestas consistentes
                "num_predict": 300,    # límite de tokens (ficha corta)
            },
        },
        timeout=TIMEOUT_GENERACION,
    )
    respuesta.raise_for_status()
    return respuesta.json()["response"].strip()


# ─────────────────────────────────────────────────────────────
# Nivel 2 — Plantilla estructurada (sin LLM, siempre disponible)
# ─────────────────────────────────────────────────────────────

_NIVELES = {3: "Alta", 2: "Media", 1: "Baja"}

_RECOMENDACIONES = {
    "Batería": "Llevar cables de arranque, multímetro y batería de repuesto.",
    "Llanta": "Llevar gata hidráulica, llave de cruz y llanta/parche de emergencia.",
    "Motor": "Llevar refrigerante, herramientas de diagnóstico y kit de remolque.",
    "Choque": "Evaluar daños estructurales; considerar grúa y kit de seguridad vial.",
    "Accidente": "Considerar grúa; priorizar la seguridad de los ocupantes.",
    "Fallo eléctrico": "Llevar multímetro, fusibles y cables de repuesto.",
    "Sin combustible": "Llevar bidón con combustible (verificar si es gasolina o diésel).",
    "Fallo de frenos": "Llevar líquido de frenos y pastillas; considerar remolque.",
}


def _generar_con_plantilla(ctx: dict) -> str:
    """Ficha estructurada SIN IA: se arma con los datos del incidente."""
    nivel = _NIVELES.get(ctx["prioridad"], "Baja")

    # Buscar una recomendación cuya clave aparezca en el nombre de la categoría
    recomendacion = "Llevar kit básico de auxilio vehicular y herramientas generales."
    for clave, texto in _RECOMENDACIONES.items():
        if clave.lower() in ctx["categoria"].lower():
            recomendacion = texto
            break

    return (
        f"RESUMEN: Incidente #{ctx['id']} reportado el {ctx['fecha']} por {ctx['cliente']}. "
        f"El cliente describe: \"{ctx['descripcion']}\". Vehículo: {ctx['vehiculo']}.\n"
        f"TIPO DE PROBLEMA: {ctx['categoria']}\n"
        f"NIVEL DE URGENCIA: {nivel} (según la prioridad de la categoría reportada)\n"
        f"RECOMENDACIÓN AL TALLER: {recomendacion}\n"
        f"EVIDENCIAS: {ctx['evidencias']}"
    )


# ─────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────

def generar_ficha(incidente) -> dict:
    """
    Genera la ficha estructurada de un incidente.

    Intenta primero con Gemma 2B (Ollama). Si no está disponible,
    usa la plantilla. SIEMPRE devuelve una ficha.

    Retorna:
        {
          "ficha": "RESUMEN: ...",
          "modelo_usado": "gemma2:2b (ollama)" | "plantilla (sin LLM)",
          "generado_en": "2026-06-11T..."
        }
    """
    ctx = _contexto_incidente(incidente)

    if ollama_disponible():
        try:
            ficha = _generar_con_ollama(ctx)
            return {
                "ficha": ficha,
                "modelo_usado": f"{OLLAMA_MODELO} (ollama)",
                "generado_en": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            # Si Ollama falla a mitad de camino, caemos a la plantilla
            logger.warning(f"[IA] Ollama falló, usando plantilla: {e}")

    return {
        "ficha": _generar_con_plantilla(ctx),
        "modelo_usado": "plantilla (sin LLM)",
        "generado_en": datetime.utcnow().isoformat(),
    }
