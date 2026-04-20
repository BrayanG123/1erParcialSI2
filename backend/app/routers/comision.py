from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.comision import ComisionRead
from app.crud.comision import (
    get_comision_por_servicio,
    get_comision_por_id,
)
from app.core.dependencies import get_current_administrador
from app.services.bitacora import BitacoraService



router = APIRouter(prefix="/comisiones", tags=["Comisiones"])



# ── ADMIN — ver comisión de un servicio ───────────────────────────────────────
@router.get("/servicio/{servicio_id}", response_model=ComisionRead)
def comision_de_servicio(
    servicio_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    comision = get_comision_por_servicio(db, servicio_id)
    if not comision:
        raise HTTPException(status_code=404, detail="Aún no hay comisión para este servicio")
    return comision


# ── ADMIN — listar todas las comisiones ───────────────────────────────────────
@router.get("/", response_model=list[ComisionRead])
def listar_comisiones(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    from app.models.comision import Comision
    return db.query(Comision).order_by(Comision.fecha_emision.desc()).all()