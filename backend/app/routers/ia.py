"""
ia.py — Endpoints del Módulo de Inteligencia Artificial.

  GET  /ia/estado                                → qué motores están disponibles
  POST /ia/clasificar-imagen                     → visión artificial (CLIP)
  POST /ia/resumen/{incidente_id}                → ficha estructurada (Gemma 2B / plantilla)
  GET  /ia/asignacion-inteligente/{incidente_id} → mejor taller para el incidente

IMPORTANTE: los modelos se cargan de forma PEREZOSA. El backend arranca
y funciona aunque torch/transformers no estén instalados — solo los
endpoints de visión devolverán un error claro indicando qué instalar.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_administrador, get_current_usuario
from app.database import get_db
from app.models.categoria import Categoria
from app.models.evidencia import Evidencia, TipoEvidencia
from app.models.incidente import Incidente
from app.models.procesamiento_ia import EstadoProcesamiento, ProcesamientoIA
from app.models.usuario import Usuario
from app.services.bitacora import BitacoraService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ia", tags=["Inteligencia Artificial"])


# ─────────────────────────────────────────────────────────────
# Estado de los motores de IA
# ─────────────────────────────────────────────────────────────

@router.get("/estado")
def estado_ia(usuario: Usuario = Depends(get_current_usuario)):
    """
    Diagnóstico rápido: qué motores de IA están listos para usarse.
    Útil para verificar la instalación sin gastar recursos
    (NO carga ningún modelo).
    """
    from app.services.ia import clasificador_imagen, generador_resumen

    ollama_ok = generador_resumen.ollama_disponible()
    return {
        "vision_artificial": {
            "dependencias_instaladas": clasificador_imagen.dependencias_instaladas(),
            "modelo_en_memoria": clasificador_imagen.modelo_cargado(),
            "modelo": clasificador_imagen.NOMBRE_MODELO,
            "nota": "El modelo se carga en RAM (~600 MB) la primera vez que se clasifica una imagen.",
        },
        "generador_resumen": {
            "ollama_corriendo": ollama_ok,
            "modelo_descargado": generador_resumen.modelo_descargado() if ollama_ok else False,
            "modelo": generador_resumen.OLLAMA_MODELO,
            "nota": "Si Ollama no está corriendo, se usa una plantilla estructurada (sin LLM).",
        },
        "asignador_inteligente": {
            "disponible": True,
            "nota": "Algoritmo de puntuación multi-criterio. No requiere modelo ni RAM extra.",
        },
    }


# ─────────────────────────────────────────────────────────────
# 1) Clasificación de imágenes (visión artificial)
# ─────────────────────────────────────────────────────────────

@router.post("/clasificar-imagen")
async def clasificar_imagen_endpoint(
    archivo: Optional[UploadFile] = File(default=None),
    incidente_id: Optional[int] = Query(default=None),
    actualizar_categoria: bool = Query(
        default=False,
        description="Si true y se pasó incidente_id, actualiza la categoría del incidente con el resultado",
    ),
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Clasifica una foto de incidente en: bateria / llanta / choque / motor / otros.

    Dos formas de uso:
      a) Subir una imagen directamente (campo 'archivo')
      b) Pasar ?incidente_id=N → usa la foto del incidente (foto_incidente
         o su primera evidencia de tipo foto)
    """
    from app.services.ia import clasificador_imagen

    imagen_bytes = None
    imagen_url = None
    incidente = None

    # ── Obtener la imagen ──
    if archivo is not None:
        imagen_bytes = await archivo.read()
    elif incidente_id is not None:
        incidente = db.query(Incidente).filter(Incidente.id == incidente_id).first()
        if not incidente:
            raise HTTPException(status_code=404, detail="Incidente no encontrado")

        # Prioridad: foto principal del incidente → primera evidencia foto
        if incidente.foto_incidente:
            imagen_url = incidente.foto_incidente
        else:
            evidencia = (
                db.query(Evidencia)
                .filter(
                    Evidencia.incidente_id == incidente_id,
                    Evidencia.tipo == TipoEvidencia.foto,
                )
                .first()
            )
            if evidencia:
                imagen_url = evidencia.url_archivo

        if not imagen_url:
            raise HTTPException(
                status_code=400,
                detail="El incidente no tiene fotos para clasificar",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Envía una imagen (campo 'archivo') o un ?incidente_id=N",
        )

    # ── Clasificar (aquí se carga CLIP la primera vez) ──
    try:
        resultado = clasificador_imagen.clasificar_imagen(
            imagen_bytes=imagen_bytes, imagen_url=imagen_url
        )
    except RuntimeError as e:
        # Dependencias de IA no instaladas → mensaje claro, no un error 500 críptico
        raise HTTPException(status_code=503, detail=str(e))

    # ── Actualizar la categoría del incidente (opcional) ──
    if actualizar_categoria and incidente is not None:
        clave_bd = clasificador_imagen.CATEGORIA_IA_A_BD.get(resultado["categoria"])
        if clave_bd:
            categoria = (
                db.query(Categoria)
                .filter(Categoria.nombre.ilike(f"%{clave_bd}%"))
                .first()
            )
            if categoria:
                incidente.categoria_id = categoria.id
                db.commit()
                resultado["categoria_actualizada"] = categoria.nombre

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="IA_CLASIFICAR_IMAGEN",
        descripcion=f"Imagen clasificada como '{resultado['categoria']}' "
                    f"(confianza {resultado['confianza']})"
                    + (f" para incidente #{incidente_id}" if incidente_id else ""),
        entidad_afectada="incidente",
    )
    return resultado


# ─────────────────────────────────────────────────────────────
# 2) Generación de ficha / resumen del incidente
# ─────────────────────────────────────────────────────────────

@router.post("/resumen/{incidente_id}")
def generar_resumen_endpoint(
    incidente_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Genera la ficha estructurada del incidente y la guarda en:
      - incidente.resumen_ia (para mostrarla en las apps)
      - tabla procesamientos_ia (auditoría de cada ejecución)

    Usa Gemma 2B vía Ollama si está corriendo; si no, plantilla estructurada.
    """
    from app.services.ia import generador_resumen

    incidente = db.query(Incidente).filter(Incidente.id == incidente_id).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    # Registro de auditoría: empieza como 'pendiente'
    procesamiento = ProcesamientoIA(
        incidente_id=incidente_id,
        estado=EstadoProcesamiento.pendiente,
    )
    db.add(procesamiento)
    db.flush()

    try:
        resultado = generador_resumen.generar_ficha(incidente)

        # Guardar la ficha en el incidente y cerrar el registro de auditoría
        incidente.resumen_ia = resultado["ficha"]
        procesamiento.estado = EstadoProcesamiento.completado
        procesamiento.resumen_generado = resultado["ficha"]
        procesamiento.modelo_usado = resultado["modelo_usado"]
        procesamiento.fecha_fin = datetime.utcnow()
        db.commit()

        BitacoraService.registrar(
            db=db,
            usuario_id=usuario.id,
            accion="IA_GENERAR_RESUMEN",
            descripcion=f"Ficha IA generada para incidente #{incidente_id} "
                        f"con {resultado['modelo_usado']}",
            entidad_afectada="incidente",
        )
        return {
            "incidente_id": incidente_id,
            "ficha": resultado["ficha"],
            "modelo_usado": resultado["modelo_usado"],
            "procesamiento_id": procesamiento.id,
        }

    except Exception as e:
        procesamiento.estado = EstadoProcesamiento.error
        procesamiento.mensaje_error = str(e)
        procesamiento.fecha_fin = datetime.utcnow()
        db.commit()
        logger.error(f"[IA] Error generando resumen del incidente {incidente_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando el resumen: {e}")


# ─────────────────────────────────────────────────────────────
# 3) Asignación inteligente de taller
# ─────────────────────────────────────────────────────────────

@router.get("/asignacion-inteligente/{incidente_id}")
def asignacion_inteligente_endpoint(
    incidente_id: int,
    top: int = Query(default=5, ge=1, le=20, description="Cuántos candidatos devolver"),
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Evalúa todos los talleres activos contra el incidente y devuelve la
    lista de candidatos rankeados + el mejor taller, con el desglose de
    puntaje por criterio (distancia, especialidad, disponibilidad,
    carga y calificación).
    """
    from app.services.ia import asignador_inteligente

    incidente = db.query(Incidente).filter(Incidente.id == incidente_id).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    resultado = asignador_inteligente.asignar_taller_inteligente(db, incidente, top=top)

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="IA_ASIGNACION_INTELIGENTE",
        descripcion=f"Asignación inteligente para incidente #{incidente_id}: "
                    + (f"taller #{resultado['seleccionado']['taller_id']} seleccionado"
                       if resultado["seleccionado"] else "sin candidatos"),
        entidad_afectada="incidente",
    )
    return resultado
