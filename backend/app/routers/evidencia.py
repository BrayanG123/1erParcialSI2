from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario, Mecanico
from app.models.asignacion_servicio import AsignacionServicio
from app.schemas.evidencia import EvidenciaCreate, EvidenciaRead
from app.crud.evidencia import crear_evidencia, get_evidencias_de_incidente
from app.crud.incidente import get_incidente_por_id
from app.core.dependencies import get_current_cliente, get_current_administrador
from app.services.bitacora import BitacoraService

router = APIRouter(prefix="/evidencias", tags=["Evidencias"])

@router.post("/", response_model=EvidenciaRead, status_code=status.HTTP_201_CREATED)
def subir_evidencia(
    datos: EvidenciaCreate,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    incidente = get_incidente_por_id(db, datos.incidente_id)
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
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

@router.get("/incidente/{incidente_id}", response_model=list[EvidenciaRead])
def evidencias_de_incidente(
    incidente_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    # Verificar que el incidente pertenece al taller del admin
    incidente = (
        db.query(AsignacionServicio)
        .join(AsignacionServicio.mecanico)
        .filter(
            AsignacionServicio.incidente_id == incidente_id,
            Mecanico.taller_id == taller_id
        )
        .first()
    )
    if not incidente:
        raise HTTPException(status_code=403, detail="Este incidente no pertenece a tu taller")

    return get_evidencias_de_incidente(db, incidente_id)