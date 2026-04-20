from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.models.asignacion_servicio import EstadoAsignacion
from app.schemas.servicio_realizado import ServicioRealizadoCreate, ServicioRealizadoRead
from app.crud.asignacion_servicio import get_asignacion_por_id, actualizar_estado_asignacion
from app.crud.servicio_realizado import (
    crear_servicio_realizado,
    get_servicio_por_asignacion,
    get_servicio_por_id,
    get_servicios_de_mecanico,
)
from app.schemas.asignacion_servicio import AsignacionEstadoUpdate
from app.core.dependencies import get_current_mecanico, get_current_administrador
from app.services.bitacora import BitacoraService


router = APIRouter(prefix="/servicios-realizados", tags=["Servicios Realizados"])



# ── MECÁNICO — registrar el servicio al completar su asignación ───────────────
@router.post(
    "/asignacion/{asignacion_id}",
    response_model=ServicioRealizadoRead,
    status_code=status.HTTP_201_CREATED,
)
def registrar_servicio(
    asignacion_id: int,
    datos: ServicioRealizadoCreate,
    usuario: Usuario = Depends(get_current_mecanico),
    db: Session = Depends(get_db),
):
    """
    El mecánico registra el servicio realizado al terminar su asignación.
    Esto cambia automáticamente el estado de la asignación a 'completada'.
    """
    asignacion = get_asignacion_por_id(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    # Solo el mecánico asignado puede registrar el servicio
    mecanico = usuario.perfil_mecanico
    if asignacion.mecanico_id != mecanico.id:
        raise HTTPException(status_code=403, detail="Esta asignación no es tuya")

    # Solo se puede registrar si la asignación está en_servicio
    if asignacion.estado != EstadoAsignacion.en_servicio:
        raise HTTPException(
            status_code=400,
            detail=f"Solo puedes registrar el servicio cuando estás 'en_servicio'. "
                   f"Estado actual: '{asignacion.estado.value}'"
        )

    # Verificar que no exista ya un ServicioRealizado para esta asignación
    existente = get_servicio_por_asignacion(db, asignacion_id)
    if existente:
        raise HTTPException(status_code=400, detail="Esta asignación ya tiene un servicio registrado")

    # Crear el registro del servicio
    servicio = crear_servicio_realizado(db, asignacion_id, datos)

    # Marcar la asignación como completada automáticamente
    actualizar_estado_asignacion(
        db, asignacion, AsignacionEstadoUpdate(estado=EstadoAsignacion.completada)
    )

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="REGISTRAR_SERVICIO",
        descripcion=f"Servicio #{servicio.id} registrado para asignación #{asignacion_id}",
    )
    return servicio



# ── MECÁNICO — ver mis servicios realizados ───────────────────────────────────
@router.get("/mis-servicios", response_model=list[ServicioRealizadoRead])
def mis_servicios(
    usuario: Usuario = Depends(get_current_mecanico),
    db: Session = Depends(get_db),
):
    mecanico = usuario.perfil_mecanico
    return get_servicios_de_mecanico(db, mecanico.id)



# ── ADMIN — ver servicio de una asignación específica ────────────────────────
@router.get("/asignacion/{asignacion_id}", response_model=ServicioRealizadoRead)
def servicio_de_asignacion(
    asignacion_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    servicio = get_servicio_por_asignacion(db, asignacion_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Esta asignación no tiene servicio registrado aún")
    return servicio



# ── ADMIN — ver todos los servicios realizados ────────────────────────────────
@router.get("/", response_model=list[ServicioRealizadoRead])
def listar_servicios(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    from app.models.servicio_realizado import ServicioRealizado as SR
    return db.query(SR).order_by(SR.fecha_realizado.desc()).all()
