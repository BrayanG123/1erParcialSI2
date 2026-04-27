from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.evidencia import EvidenciaCreate, EvidenciaRead
from app.crud.evidencia import crear_evidencia, get_evidencias_de_incidente
from app.crud.incidente import get_incidente_por_id
from app.core.dependencies import (
    get_current_cliente, 
    get_current_administrador,
)
from app.services.bitacora import BitacoraService
from app.models.evidencia import TipoEvidencia
from app.schemas.evidencia import EvidenciaCreate, EvidenciaRead
from app.services.cloudinary_service import subir_imagen




router = APIRouter(prefix="/evidencias", tags=["Evidencias"])



# ── CLIENTE — subir evidencia a un incidente ─────────────────────────────────
@router.post("/", response_model=EvidenciaRead, status_code=status.HTTP_201_CREATED)
def subir_evidencia(
    datos: EvidenciaCreate,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    incidente = get_incidente_por_id(db, datos.incidente_id)
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    # Solo el cliente dueño puede subir evidencia
    if incidente.cliente.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Este incidente no es tuyo")

    evidencia = crear_evidencia(db, datos)

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="SUBIR_EVIDENCIA",
        descripcion=f"Evidencia #{evidencia.id} ({datos.tipo.value}) subida al incidente #{datos.incidente_id}",
    )
    return evidencia


# ── ADMIN — ver evidencias de un incidente ───────────────────────────────────
@router.get("/admin/incidente/{incidente_id}", response_model=list[EvidenciaRead])
def listar_admin(
    incidente_id: int,
    _: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    return get_evidencias_de_incidente(db, incidente_id)


# ── CLIENTE — ver evidencia
@router.get("/incidente/{incidente_id}", response_model=list[EvidenciaRead])
def listar_fotos(
    incidente_id: int,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    incidente = get_incidente_por_id(db, incidente_id)
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    if incidente.cliente.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Este incidente no es tuyo")
    return get_evidencias_de_incidente(db, incidente_id)


@router.post(
    "/incidente/{incidente_id}/foto",
    response_model=EvidenciaRead,
    status_code=status.HTTP_201_CREATED,
)
def subir_foto(
    incidente_id: int,
    foto: UploadFile = File(...),
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    incidente = get_incidente_por_id(db, incidente_id)
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    if incidente.cliente.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Este incidente no es tuyo")

    try:
        url = subir_imagen(foto, carpeta="evidencias")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return crear_evidencia(
        db,
        EvidenciaCreate(incidente_id=incidente_id, tipo=TipoEvidencia.foto, url_archivo=url),
    )
