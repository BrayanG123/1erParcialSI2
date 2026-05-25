# para la ia
from app.services.ia.azure_speech_service import transcribir_audio
from app.services.ia.procesador_groq import diagnosticar_vehiculo
from app.schemas.procesamiento_ia import ProcesamientoIARead


from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from app.services.cloudinary_service import subir_imagen, subir_audio
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario, RolUsuario
from app.schemas.incidente import IncidenteCreate, IncidenteRead, IncidenteUpdate
from app.models.incidente import Incidente as IncidenteModel
from app.models.asignacion_servicio import AsignacionServicio
from app.models.usuario import Mecanico
from app.crud.incidente import (
    crear_incidente,
    get_incidentes_de_cliente,
    get_incidentes_disponibles,
    actualizar_incidente,
)
from app.core.dependencies import (
    get_current_cliente,
    get_current_administrador,
    get_current_usuario,
)
from app.services.bitacora import BitacoraService
from app.crud.asignacion_servicio import get_asignacion_por_incidente
from app.schemas.asignacion_servicio import AsignacionRead



router = APIRouter(prefix="/incidentes", tags=["Incidentes"])


# CLIENTE — reportar un incidente
# ─────────────────────────────────────────────────────────────────────────────
@router.post("", response_model=IncidenteRead, status_code=status.HTTP_201_CREATED)
def reportar_incidente(
    datos: IncidenteCreate,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    cliente = usuario.perfil_cliente
    incidente = crear_incidente(db, cliente.id, datos)
    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="REPORTAR_INCIDENTE",
        descripcion=f"Incidente #{incidente.id} reportado",
    )
    return incidente


# CLIENTE — mis incidentes ───────────────
@router.get("/mis-incidentes", response_model=list[IncidenteRead])
def mis_incidentes(
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    cliente = usuario.perfil_cliente
    return get_incidentes_de_cliente(db, cliente.id)


# CLIENTE — subir foto a un incidente propio ─────────────────
@router.post("/{incidente_id}/foto", response_model=IncidenteRead)
def subir_foto_incidente(
    incidente_id: int,
    foto: UploadFile = File(...),
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """El cliente sube una foto a su incidente recién creado."""
    incidente = get_incidente_por_id(db, incidente_id)
    if not incidente or incidente.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    try:
        url = subir_imagen(foto, carpeta="incidentes")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    incidente.foto_incidente = url
    db.commit()
    db.refresh(incidente)
    return incidente


# CLIENTE — subir audio descriptivo a un incidente propio ─────────────────
@router.post("/{incidente_id}/audio", response_model=IncidenteRead)
def subir_audio_incidente(
    incidente_id: int,
    audio: UploadFile = File(...),
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """El cliente sube un audio describiendo su problema."""
    incidente = get_incidente_por_id(db, incidente_id)
    if not incidente or incidente.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    try:
        url = subir_audio(audio, carpeta="incidentes/audios")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    incidente.audio_descripcion = url
    db.commit()
    db.refresh(incidente)
    return incidente


# ── CLIENTE — transcribir audio y generar diagnóstico ──────────────────────────
@router.post(
    "/{incidente_id}/analizar-audio",
    response_model=ProcesamientoIARead,
    summary="Transcribe el audio del incidente y genera un diagnóstico con Azure IA",
)
def analizar_audio_incidente(
    incidente_id: int,
    audio: UploadFile = File(..., description="Archivo de audio WAV u OGG (máx. 60 segundos)"),
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """
    Flujo completo:
    1. Lee el audio subido por el cliente.
    2. Lo envía a Azure Speech to Text → obtiene el texto transcrito.
    3. Envía el texto a Google Gemini → obtiene diagnóstico vehicular.
    4. Guarda el diagnóstico en incidente.resumen_ia.
    5. Devuelve el registro ProcesamientoIA con el resultado.
    """
    incidente = get_incidente_por_id(db, incidente_id)
    if not incidente or incidente.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    # Leer el audio en memoria
    audio_bytes = audio.file.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="El archivo de audio está vacío")

    # Paso 1 — Transcribir con Azure Speech
    try:
        texto_transcrito = transcribir_audio(
            audio_bytes=audio_bytes,
            content_type=audio.content_type or "audio/wav",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=f"Error al transcribir audio: {e}")

    if not texto_transcrito:
        raise HTTPException(
            status_code=422,
            detail="No se pudo extraer texto del audio. Intenta grabar de nuevo con más claridad.",
        )

    # Paso 2 — Diagnosticar con Google Gemini
    procesamiento = diagnosticar_vehiculo(
        db=db,
        incidente_id=incidente_id,
        texto=texto_transcrito,
    )

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="ANALIZAR_AUDIO_IA",
        descripcion=f"Incidente #{incidente_id} analizado con Azure Speech + Gemini",
    )

    return procesamiento


# ── CLIENTE — generar diagnóstico desde texto ─────────────────────────────────
@router.post(
    "/{incidente_id}/analizar-texto",
    response_model=ProcesamientoIARead,
    summary="Genera un diagnóstico vehicular desde una descripción de texto",
)
def analizar_texto_incidente(
    incidente_id: int,
    descripcion: str = Form(..., description="Descripción del problema en texto libre"),
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """
    Recibe una descripción de texto del cliente y la envía directamente
    a Google Gemini para generar el diagnóstico.
    """
    incidente = get_incidente_por_id(db, incidente_id)
    if not incidente or incidente.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    if not descripcion.strip():
        raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")

    procesamiento = diagnosticar_vehiculo(
        db=db,
        incidente_id=incidente_id,
        texto=descripcion,
    )

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="ANALIZAR_TEXTO_IA",
        descripcion=f"Incidente #{incidente_id} analizado con texto por Gemini",
    )

    return procesamiento


# CLIENTE — ver la asignación de su propio incidente
@router.get("/{incidente_id}/asignacion", response_model=AsignacionRead)
def obtener_asignacion_de_incidente(
    incidente_id: int,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """El cliente consulta si su incidente ya tiene mecánico asignado."""
    incidente = get_incidente_por_id(db, incidente_id)
    if not incidente or incidente.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    asignacion = get_asignacion_por_incidente(db, incidente_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Sin asignación aún")

    return asignacion


# CLIENTE — cancelar un incidente propio
# ─────────────────────────────────────────────────────────────────────────────




# ── ADMIN — ver incidentes disponibles (para aceptar) 
@router.get("/disponibles", response_model=list[IncidenteRead])
def incidentes_disponibles(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    return get_incidentes_disponibles(db)


# ADMIN — listar incidentes de SU taller
@router.get("/", response_model=list[IncidenteRead])
def listar_todos_los_incidentes(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    return (
        db.query(IncidenteModel)
        .join(IncidenteModel.asignacion)
        .join(AsignacionServicio.mecanico)
        .filter(Mecanico.taller_id == taller_id)
        .order_by(IncidenteModel.fecha_hora.desc())
        .all()
    )


# ADMIN — actualizar un incidente (resumen IA, categoría)
@router.patch("/{incidente_id}", response_model=IncidenteRead)
def actualizar_un_incidente(
    incidente_id: int,
    datos: IncidenteUpdate,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    incidente = (
        db.query(IncidenteModel)
        .join(IncidenteModel.asignacion)
        .join(AsignacionServicio.mecanico)
        .filter(
            IncidenteModel.id == incidente_id,
            Mecanico.taller_id == taller_id
        )
        .first()
    )
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado o no pertenece a tu taller")
    return actualizar_incidente(db, incidente, datos)


# COMPARTIDO — obtener un incidente por ID
@router.get("/{incidente_id}", response_model=IncidenteRead)
def obtener_incidente(
    incidente_id: int,
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    """
    Admin: puede ver cualquier incidente.
    Cliente: solo puede ver sus propios incidentes.
    """
    incidente = get_incidente_por_id(db, incidente_id)
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    
    # Si es cliente, verificar que le pertenece
    if usuario.rol == RolUsuario.cliente:
        if incidente.cliente_id != usuario.perfil_cliente.id:
            raise HTTPException(status_code=403, detail="No autorizado")
        
    return incidente