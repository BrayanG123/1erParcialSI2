from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario, Mecanico
from app.models.comision import Comision
from app.models.asignacion_servicio import AsignacionServicio
from app.models.servicio_realizado import ServicioRealizado
from app.schemas.comision import ComisionRead
from app.crud.comision import get_comision_por_servicio, get_comision_por_id
from app.core.dependencies import get_current_administrador

router = APIRouter(prefix="/comisiones", tags=["Comisiones"])

@router.get("/servicio/{servicio_id}", response_model=ComisionRead)
def comision_de_servicio(
    servicio_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    # Verificar que el servicio pertenece al taller
    servicio = (
        db.query(ServicioRealizado)
        .join(ServicioRealizado.asignacion)
        .join(AsignacionServicio.mecanico)
        .filter(
            ServicioRealizado.id == servicio_id,
            Mecanico.taller_id == taller_id
        )
        .first()
    )
    if not servicio:
        raise HTTPException(status_code=403, detail="Este servicio no pertenece a tu taller")

    comision = get_comision_por_servicio(db, servicio_id)
    if not comision:
        raise HTTPException(status_code=404, detail="Aún no hay comisión para este servicio")
    return comision

@router.get("/", response_model=list[ComisionRead])
def listar_comisiones(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    return (
        db.query(Comision)
        .join(ServicioRealizado, ServicioRealizado.id == Comision.servicio_id)  # ← fix
        .join(AsignacionServicio, AsignacionServicio.id == ServicioRealizado.asignacion_id)
        .join(Mecanico, Mecanico.id == AsignacionServicio.mecanico_id)
        .filter(Mecanico.taller_id == taller_id)
        .order_by(Comision.fecha_emision.desc())
        .all()
    )