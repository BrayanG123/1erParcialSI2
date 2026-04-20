from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.calificacion import CalificacionCreate, CalificacionRead
from app.crud.calificacion import (
    crear_calificacion,
    get_calificacion_por_servicio,
    get_calificaciones_de_mecanico,
)
from app.crud.servicio_realizado import get_servicio_por_id
from app.core.dependencies import get_current_cliente, get_current_administrador
from app.services.bitacora import BitacoraService



router = APIRouter(prefix="/calificaciones", tags=["Calificaciones"])



# ── CLIENTE — calificar un servicio ──────────────────────────────────────────
@router.post("/", response_model=CalificacionRead, status_code=status.HTTP_201_CREATED)
def calificar_servicio(
    datos: CalificacionCreate,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """El cliente califica el servicio recibido (1-5 estrellas)."""
    servicio = get_servicio_por_id(db, datos.servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    # Verificar que el servicio pertenece al cliente
    incidente = servicio.asignacion.incidente
    if incidente.cliente.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Este servicio no es tuyo")

    # Verificar que no haya calificación previa
    existente = get_calificacion_por_servicio(db, datos.servicio_id)
    if existente:
        raise HTTPException(status_code=400, detail="Ya calificaste este servicio")

    calificacion = crear_calificacion(db, datos)

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="CALIFICAR_SERVICIO",
        descripcion=f"Servicio #{datos.servicio_id} calificado con {datos.puntuacion}/5",
    )
    return calificacion



# ── CLIENTE / ADMIN — ver calificación de un servicio ────────────────────────
@router.get("/servicio/{servicio_id}", response_model=CalificacionRead)
def calificacion_de_servicio(
    servicio_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    cal = get_calificacion_por_servicio(db, servicio_id)
    if not cal:
        raise HTTPException(status_code=404, detail="Este servicio aún no tiene calificación")
    return cal



# ── ADMIN — ver calificaciones de un mecánico ────────────────────────────────
@router.get("/mecanico/{mecanico_id}", response_model=list[CalificacionRead])
def calificaciones_de_mecanico(
    mecanico_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    return get_calificaciones_de_mecanico(db, mecanico_id)