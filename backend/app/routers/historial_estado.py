from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.models.historial_estado import HistorialEstado
from app.schemas.historial_estado import HistorialEstadoRead
from app.core.dependencies import get_current_administrador, get_current_mecanico



router = APIRouter(prefix="/historial-estados", tags=["Historial de Estados"])



# ── ADMIN / MECÁNICO — ver historial de una asignación ───────────────────────
@router.get("/asignacion/{asignacion_id}", response_model=list[HistorialEstadoRead])
def historial_de_asignacion(
    asignacion_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    return (
        db.query(HistorialEstado)
        .filter(HistorialEstado.asignacion_id == asignacion_id)
        .order_by(HistorialEstado.fecha_cambio)
        .all()
    )