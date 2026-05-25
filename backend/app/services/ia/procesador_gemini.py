import json
from datetime import datetime

import google.generativeai as genai
from sqlalchemy.orm import Session

from app.config import settings
from app.models.procesamiento_ia import ProcesamientoIA, EstadoProcesamiento
from app.models.incidente import Incidente


# ── Función principal ─────────────────────────────────────────────────────────

def diagnosticar_vehiculo(
    db: Session,
    incidente_id: int,
    texto: str,
) -> ProcesamientoIA:
    """
    Analiza el texto (descripción directa o transcripción de audio) y genera
    un diagnóstico vehicular usando Google Gemini.

    - Actualiza incidente.resumen_ia con el diagnóstico generado.
    - Asigna categoria_id si Gemini sugiere una categoría conocida.
    - Crea y devuelve un registro ProcesamientoIA con el resultado.
    """
    incidente = db.query(Incidente).filter(Incidente.id == incidente_id).first()
    if not incidente:
        raise ValueError(f"Incidente {incidente_id} no encontrado")

    procesamiento = ProcesamientoIA(
        incidente_id=incidente_id,
        modelo_usado=settings.GEMINI_MODEL,
        fecha_inicio=datetime.utcnow(),
    )
    db.add(procesamiento)
    db.flush()

    try:
        if not settings.GEMINI_API_KEY:
            # ── Modo MOCK (sin API key configurada) 
            resumen = f"[MOCK] Diagnóstico para: {texto[:100]}"
            categoria_sugerida = "otro"
        else:
            # ── Modo REAL (Google Gemini) 
            resumen, categoria_sugerida = _llamar_gemini(texto)

        # Persistir el resumen en el incidente
        incidente.resumen_ia = resumen
        _asignar_categoria(db, incidente, categoria_sugerida)

        procesamiento.estado = EstadoProcesamiento.completado
        procesamiento.resumen_generado = resumen
        procesamiento.fecha_fin = datetime.utcnow()

    except Exception as exc:
        procesamiento.estado = EstadoProcesamiento.error
        procesamiento.mensaje_error = str(exc)
        procesamiento.fecha_fin = datetime.utcnow()
        # No re-lanzamos: el endpoint puede leer el estado del procesamiento

    db.commit()
    db.refresh(procesamiento)
    return procesamiento


# ── Llamada a Google Gemini ───────────────────────────────────────────────────

def _llamar_gemini(descripcion: str) -> tuple[str, str]:
    """
    Llama a Google Gemini y devuelve (resumen_tecnico, categoria_sugerida).
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    modelo = genai.GenerativeModel(settings.GEMINI_MODEL)

    prompt = _construir_prompt(descripcion)
    respuesta = modelo.generate_content(prompt)
    contenido_raw = respuesta.text.strip()

    # Limpiar bloques markdown que Gemini a veces incluye (```json ... ```)
    if contenido_raw.startswith("```"):
        lineas = contenido_raw.split("\n")
        contenido_raw = "\n".join(lineas[1:-1])

    try:
        data = json.loads(contenido_raw)
    except json.JSONDecodeError:
        # Si Gemini no devolvió JSON válido, guardar el texto como resumen
        return contenido_raw[:500], "otro"

    resumen = data.get("resumen", "Diagnóstico no disponible")
    categoria = data.get("categoria_sugerida", "otro").lower().strip()
    return resumen, categoria


def _construir_prompt(descripcion: str) -> str:
    return (
        "Eres un mecánico experto que diagnostica fallas vehiculares. "
        "Responde siempre en español.\n\n"
        f"El cliente describe el problema de su vehículo así:\n\n"
        f'"{descripcion}"\n\n'
        "Analiza este problema y responde ÚNICAMENTE con un JSON con exactamente estas dos claves:\n"
        '{ "resumen": "descripción técnica breve del problema en 1-2 oraciones", '
        '"categoria_sugerida": "pinchazo | bateria | motor | frenos | otro" }\n'
        "Elige la categoria_sugerida que mejor describe el problema. "
        "No incluyas texto adicional fuera del JSON."
    )


# ── Asignar categoría ─────────────────────────────────────────────────────────

def _asignar_categoria(db: Session, incidente: Incidente, nombre_categoria: str) -> None:
    """
    Busca una categoría en BD cuyo nombre coincida con lo que sugirió la IA
    y la asigna al incidente.
    """
    from app.models.categoria import Categoria

    categoria = (
        db.query(Categoria)
        .filter(Categoria.nombre.ilike(f"%{nombre_categoria}%"))
        .first()
    )
    if categoria:
        incidente.categoria_id = categoria.id
