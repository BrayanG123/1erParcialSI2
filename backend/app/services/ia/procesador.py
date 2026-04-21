# import json
# import os
# from datetime import datetime
# from sqlalchemy.orm import Session

# from app.models.procesamiento_ia import ProcesamientoIA, EstadoProcesamiento
# from app.models.incidente import Incidente
# from app.models.evidencia import Evidencia
# from app.models.categoria import Categoria
# from app.services.ia.prompt_builder import construir_prompt



# # Nombre del modelo a usar
# MODELO_IA = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# def procesar_incidente(db: Session, incidente_id: int) -> ProcesamientoIA:
#     """
#     Analiza las evidencias del incidente y actualiza resumen_ia y categoria_id.
#     Crea y devuelve un registro ProcesamientoIA con el resultado.
#     """
#     incidente = db.query(Incidente).filter(Incidente.id == incidente_id).first()
#     if not incidente:
#         raise ValueError(f"Incidente {incidente_id} no encontrado")

#     evidencias = (
#         db.query(Evidencia)
#         .filter(Evidencia.incidente_id == incidente_id)
#         .all()
#     )

#     # Crear el registro de procesamiento en estado "pendiente"
#     procesamiento = ProcesamientoIA(
#         incidente_id=incidente_id,
#         modelo_usado=MODELO_IA,
#     )
#     db.add(procesamiento)
#     db.flush()

#     try:
#         resumen, categoria_sugerida = _llamar_ia(incidente, evidencias)

#         # Actualizar el incidente con los resultados
#         incidente.resumen_ia = resumen
#         _asignar_categoria(db, incidente, categoria_sugerida)

#         # Marcar evidencias como procesadas
#         for e in evidencias:
#             e.procesado_ia = 1

#         procesamiento.estado           = EstadoProcesamiento.completado
#         procesamiento.resumen_generado = resumen
#         procesamiento.fecha_fin        = datetime.utcnow()

#     except Exception as exc:
#         procesamiento.estado        = EstadoProcesamiento.error
#         procesamiento.mensaje_error = str(exc)
#         procesamiento.fecha_fin     = datetime.utcnow()

#     db.commit()
#     db.refresh(procesamiento)
#     return procesamiento


# def _llamar_ia(incidente: Incidente, evidencias: list[Evidencia]) -> tuple[str, str]:
#     """
#     Llama a la API de OpenAI. Si OPENAI_API_KEY no está configurada,
#     usa una respuesta mock para desarrollo.
#     """
#     api_key = os.getenv("OPENAI_API_KEY")

#     if not api_key:
#         # ── Modo MOCK (sin API key) ───────────────────────────────────────────
#         return (
#             f"[MOCK] Problema detectado en el vehículo: {incidente.descripcion[:80]}",
#             "otro",
#         )

#     # ── Modo REAL (con OpenAI) ────────────────────────────────────────────────
#     try:
#         from openai import OpenAI
#     except ImportError:
#         raise RuntimeError(
#             "La librería 'openai' no está instalada. "
#             "Ejecuta: .\\venv\\Scripts\\pip install openai"
#         )

#     prompt = construir_prompt(incidente.descripcion, evidencias)
#     client = OpenAI(api_key=api_key)

#     respuesta = client.chat.completions.create(
#         model=MODELO_IA,
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.3,
#     )

#     texto = respuesta.choices[0].message.content.strip()
#     datos = json.loads(texto)   # el prompt pide JSON estricto
#     return datos["resumen"], datos.get("categoria_sugerida", "otro")



# def _asignar_categoria(db: Session, incidente: Incidente, nombre_sugerido: str) -> None:
#     """Busca la categoría por nombre y la asigna al incidente si existe."""
#     categoria = (
#         db.query(Categoria)
#         .filter(Categoria.nombre.ilike(f"%{nombre_sugerido}%"))
#         .first()
#     )
#     if categoria:
#         incidente.categoria_id = categoria.id