"""
reporte_dinamico.py — Endpoints del módulo "Reportes Dinámicos por Prompts".

Fase 1 (actual): el cliente envía el JSON QBE directamente.
Fase 2 (futura): un endpoint adicional recibirá texto en lenguaje natural,
lo pasará al LLM (Structured Outputs) y el JSON resultante entrará por el
mismo motor ejecutar_qbe() — por eso el motor vive en services/, no aquí.
"""
import logging
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_administrador
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.reporte_qbe import QBERequest, QBEResponse
from app.services.qbe_engine import describir_esquema, ejecutar_qbe

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reportes", tags=["Reportes Dinámicos"])


def _tenant_del_admin(usuario: Usuario) -> int:
    """
    Tenant del administrador (desde su perfil en BD).

    AISLAMIENTO MULTI-TENANT: los reportes SIEMPRE se filtran por el
    tenant del taller que consulta. Si el admin aún no tiene tenant,
    se rechaza con 403 — jamás se devuelven datos de todos los talleres.
    (Las entidades globales, como 'incidentes', no llevan tenant por diseño.)
    """
    tenant_id = (
        usuario.perfil_administrador.tenant_id
        if usuario.perfil_administrador else None
    )
    if tenant_id is None:
        raise HTTPException(
            status_code=403,
            detail="Tu cuenta no tiene un taller/tenant asignado. "
                   "Configura tu taller (o cierra sesión y vuelve a entrar).",
        )
    return tenant_id


@router.post("/qbe", response_model=QBEResponse)
def generar_reporte_qbe(
    qbe: QBERequest,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Ejecuta un reporte dinámico a partir de una estructura QBE.

    - Reporte GERENCIAL (detalle): sin group_by/agregaciones → filas individuales.
    - Reporte EJECUTIVO (agrupado): con group_by + agregaciones → totales por grupo.

    Toda consulta queda aislada al tenant del administrador autenticado.
    """
    tenant_id = _tenant_del_admin(usuario)
    return ejecutar_qbe(db, qbe, tenant_id)


@router.get("/qbe/esquema")
def obtener_esquema_qbe(
    usuario: Usuario = Depends(get_current_administrador),
):
    """
    Catálogo de entidades, campos, operadores y agregaciones disponibles.
    Este mismo esquema se inyecta al prompt del LLM en /desde-texto.
    """
    return describir_esquema()


# ─────────────────────────────────────────────────────────────
# FASE 2+3 — Reportes por lenguaje natural (texto o voz)
# ─────────────────────────────────────────────────────────────

class ReporteDesdeTextoRequest(BaseModel):
    texto: str


@router.post("/desde-texto")
def generar_reporte_desde_texto(
    datos: ReporteDesdeTextoRequest,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Recibe un prompt en lenguaje natural, lo traduce a QBE con el LLM
    (Groq / Llama 3.3) y ejecuta el reporte con el motor QBE seguro.

    Si el motor rechaza el QBE (campo inexistente, etc.), se le reenvía
    el error al LLM para que se auto-corrija (un reintento).

    Devuelve el QBE generado (para que el frontend pre-llene el
    constructor) + el resultado del reporte.
    """
    from app.services.ia.interprete_reportes import corregir_qbe, interpretar_prompt

    texto = datos.texto.strip()
    if not texto:
        raise HTTPException(status_code=400, detail="El prompt está vacío")
    if len(texto) > 1000:
        raise HTTPException(status_code=400, detail="El prompt es demasiado largo (máx. 1000 caracteres)")

    tenant_id = _tenant_del_admin(usuario)

    # 1. Lenguaje natural → QBE
    try:
        qbe, modelo = interpretar_prompt(texto)
    except RuntimeError as e:      # GROQ_API_KEY ausente
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:        # el LLM no produjo JSON válido
        raise HTTPException(status_code=422, detail=str(e))

    # 2. Ejecutar el QBE; si el motor lo rechaza, un reintento de corrección
    intento_corregido = False
    try:
        resultado = ejecutar_qbe(db, qbe, tenant_id)
    except HTTPException as e:
        if e.status_code != 400:
            raise
        logger.info(f"[IA Reportes] Motor rechazó el QBE ({e.detail}); reintentando con corrección...")
        try:
            qbe = corregir_qbe(texto, qbe, str(e.detail))
            resultado = ejecutar_qbe(db, qbe, tenant_id)   # si falla otra vez, propaga el 400
            intento_corregido = True
        except HTTPException:
            raise
        except Exception as e2:
            raise HTTPException(
                status_code=422,
                detail=f"La IA no pudo construir un reporte válido para ese prompt: {e2}",
            )

    return {
        "prompt": texto,
        "modelo_usado": modelo,
        "qbe_generado": qbe.model_dump(mode="json"),
        "auto_corregido": intento_corregido,
        "resultado": resultado,
    }


@router.post("/transcribir-audio")
async def transcribir_audio_reporte(
    archivo: UploadFile = File(...),
    usuario: Usuario = Depends(get_current_administrador),
):
    """
    Convierte el audio del micrófono a texto usando el servicio de
    Speech-to-Text ya implementado (Azure). El frontend graba en
    audio/webm (MediaRecorder), formato que Azure acepta.

    Devuelve {"texto": "..."} para que el usuario lo revise/edite
    antes de generar el reporte.
    """
    from app.services.ia.azure_speech_service import transcribir_audio

    audio_bytes = await archivo.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="El archivo de audio está vacío")

    try:
        texto = transcribir_audio(audio_bytes, archivo.content_type or "audio/webm")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if not texto:
        raise HTTPException(
            status_code=422,
            detail="No se detectó voz en el audio. Intenta hablar más cerca del micrófono.",
        )
    return {"texto": texto}


# ─────────────────────────────────────────────────────────────
# Exportación (Excel / PDF) y envío por correo
# ─────────────────────────────────────────────────────────────

_MIME_POR_FORMATO = {
    "excel": ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    "pdf":   ("pdf",  "application/pdf"),
}


def _generar_archivo_reporte(db: Session, qbe: QBERequest, tenant_id, formato: str):
    """
    Ejecuta el QBE (forzando hasta 1000 filas, el máximo del motor)
    y genera el archivo en el formato pedido.
    Devuelve (nombre_archivo, contenido_bytes, mime_type, resultado).
    """
    from app.services.reporte_exportador import generar_excel, generar_pdf

    # Para exportar queremos TODO el reporte, no una página de la UI
    qbe.pagina = 1
    qbe.tamano_pagina = 1000

    resultado = ejecutar_qbe(db, qbe, tenant_id)

    extension, mime = _MIME_POR_FORMATO[formato]
    contenido = generar_excel(resultado) if formato == "excel" else generar_pdf(resultado)
    nombre = f"reporte_{qbe.entidad}_{datetime.now().strftime('%Y%m%d_%H%M')}.{extension}"
    return nombre, contenido, mime, resultado


@router.post("/exportar")
def exportar_reporte(
    qbe: QBERequest,
    formato: Literal["excel", "pdf"] = Query(default="excel"),
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Ejecuta el QBE y devuelve el reporte como archivo descargable
    (.xlsx o .pdf). Exporta hasta 1000 filas (el tope del motor).
    """
    tenant_id = _tenant_del_admin(usuario)
    nombre, contenido, mime, _ = _generar_archivo_reporte(db, qbe, tenant_id, formato)

    return Response(
        content=contenido,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


class EnviarReporteRequest(BaseModel):
    qbe: QBERequest
    destinatario: EmailStr                       # valida que sea un email real
    formato: Literal["excel", "pdf"] = "excel"
    mensaje: Optional[str] = None                # texto opcional del remitente


@router.post("/enviar-correo")
def enviar_reporte_por_correo(
    datos: EnviarReporteRequest,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Genera el reporte (Excel o PDF) y lo envía como adjunto al correo
    indicado, usando el SMTP configurado en el .env (Gmail + App Password).
    """
    from app.services.email_service import enviar_correo, smtp_configurado

    if not smtp_configurado():
        raise HTTPException(
            status_code=503,
            detail="El servidor de correo no está configurado (SMTP_USER / "
                   "SMTP_PASSWORD en el .env). Ver REPORTES-EXPORTAR-CORREO.md.",
        )

    tenant_id = _tenant_del_admin(usuario)
    nombre, contenido, mime, resultado = _generar_archivo_reporte(
        db, datos.qbe, tenant_id, datos.formato
    )

    tipo = "Ejecutivo" if resultado["tipo_reporte"] == "agrupado" else "Gerencial"
    cuerpo = (
        f"Hola,\n\n"
        f"Se adjunta el reporte {tipo} de '{datos.qbe.entidad}' generado el "
        f"{datetime.now().strftime('%d/%m/%Y a las %H:%M')}.\n"
        f"Total de registros: {resultado['total']}.\n\n"
    )
    if datos.mensaje:
        cuerpo += f"Mensaje del remitente:\n{datos.mensaje}\n\n"
    cuerpo += "— Enviado automáticamente por la plataforma de Auxilio Vehicular."

    try:
        enviar_correo(
            destinatario=datos.destinatario,
            asunto=f"Reporte {tipo}: {datos.qbe.entidad} ({resultado['total']} registros)",
            cuerpo=cuerpo,
            adjuntos=[(nombre, contenido, mime)],
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    logger.info(f"[Reportes] {usuario.email} envió reporte '{datos.qbe.entidad}' a {datos.destinatario}")
    return {
        "enviado": True,
        "destinatario": datos.destinatario,
        "archivo": nombre,
        "total_registros": resultado["total"],
    }
