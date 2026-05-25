import json
from datetime import datetime

from groq import Groq
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
    un diagnóstico vehicular usando Groq (Llama 3.3).

    - Actualiza incidente.resumen_ia con el diagnóstico generado.
    - Asigna categoria_id si Groq sugiere una categoría conocida.
    - Crea y devuelve un registro ProcesamientoIA con el resultado.
    """
    incidente = db.query(Incidente).filter(Incidente.id == incidente_id).first()
    if not incidente:
        raise ValueError(f"Incidente {incidente_id} no encontrado")

    procesamiento = ProcesamientoIA(
        incidente_id=incidente_id,
        modelo_usado=settings.GROQ_MODEL,
        fecha_inicio=datetime.utcnow(),
    )
    db.add(procesamiento)
    db.flush()

    try:
        if not settings.GROQ_API_KEY:
            # ── Modo MOCK (sin API key configurada) ──────────────────────────
            resumen = f"[MOCK] Diagnóstico para: {texto[:100]}"
            categoria_sugerida = "otro"
        else:
            # ── Modo REAL (Groq) ──────────────────────────────────────────────
            resumen, categoria_sugerida = _llamar_groq(texto)

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


# ── Llamada a Groq ────────────────────────────────────────────────────────────

def _llamar_groq(descripcion: str) -> tuple[str, str]:
    """
    Llama a Groq (Llama 3.3) y devuelve (resumen_tecnico, categoria_sugerida).
    Fuerza la respuesta en JSON usando response_format.
    """
    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = _construir_prompt(descripcion)

    respuesta = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un mecánico experto que diagnostica fallas vehiculares. "
                    "Responde siempre en español y ÚNICAMENTE con JSON válido."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=300,
    )

    contenido_raw = respuesta.choices[0].message.content.strip()

    try:
        data = json.loads(contenido_raw)
    except json.JSONDecodeError:
        return contenido_raw[:500], "otro"

    resumen = data.get("resumen", "Diagnóstico no disponible")
    categoria = data.get("categoria_sugerida", "otro").lower().strip()
    return resumen, categoria


def _construir_prompt(descripcion: str) -> str:
    return (
        f"El cliente describe el problema de su vehículo así:\n\n"
        f'"{descripcion}"\n\n'
        "Analiza este problema y responde con un JSON con exactamente estas dos claves:\n"
        '{ "resumen": "descripción técnica breve del problema en 1-2 oraciones", '
        '"categoria_sugerida": "pinchazo | bateria | motor | frenos | otro" }\n'
        "Elige la categoria_sugerida que mejor describe el problema."
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
