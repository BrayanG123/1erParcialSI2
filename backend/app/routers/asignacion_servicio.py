from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.models.asignacion_servicio import AsignacionServicio, EstadoAsignacion
from app.models.usuario import Mecanico
from app.schemas.asignacion_servicio import (
    AsignacionCreate,
    AsignacionRead,
    AsignacionRechazar,
    AsignacionEstadoUpdate,
)
from app.crud.asignacion_servicio import (
    crear_asignacion,
    get_asignacion_por_id,
    get_asignacion_por_incidente,
    get_asignaciones_de_mecanico,
    aceptar_asignacion,
    rechazar_asignacion,
    actualizar_estado_asignacion,
)
from app.crud.incidente import get_incidente_por_id, marcar_no_disponible
from app.core.dependencies import (
    get_current_administrador,
    get_current_mecanico,
)
from app.services.bitacora import BitacoraService
from app.models.incidente import EstadoIncidente


router = APIRouter(prefix="/asignaciones", tags=["Asignaciones de Servicio"])


# ADMIN — crear una asignación
@router.post("/", response_model=AsignacionRead, status_code=status.HTTP_201_CREATED)
def crear_nueva_asignacion(
    datos: AsignacionCreate,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    existente = get_asignacion_por_incidente(db, datos.incidente_id)
    if existente and existente.estado not in (
        EstadoAsignacion.rechazada,
        EstadoAsignacion.cancelada,
    ):
        raise HTTPException(
            status_code=400,
            detail="El incidente ya tiene una asignación activa"
        )

    incidente = get_incidente_por_id(db, datos.incidente_id)
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    if incidente.estado != EstadoIncidente.disponible:
        raise HTTPException(status_code=400, detail="El incidente no está disponible")

    # Verificar que el mecánico pertenece al taller del admin
    taller_id = usuario.perfil_administrador.taller_id
    mecanico = db.query(Mecanico).filter(
        Mecanico.id == datos.mecanico_id,
        Mecanico.taller_id == taller_id
    ).first()
    if not mecanico:
        raise HTTPException(
            status_code=403,
            detail="El mecánico no pertenece a tu taller"
        )

    asignacion = crear_asignacion(db, datos)
    marcar_no_disponible(db, incidente)

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="CREAR_ASIGNACION",
        descripcion=f"Asignación #{asignacion.id} creada para incidente #{datos.incidente_id}",
    )
    return asignacion


# ADMIN — listar asignaciones de SU taller
@router.get("/", response_model=list[AsignacionRead])
def listar_asignaciones(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    return (
        db.query(AsignacionServicio)
        .join(AsignacionServicio.mecanico)
        .filter(Mecanico.taller_id == taller_id)
        .order_by(AsignacionServicio.fecha_creacion.desc())
        .all()
    )


# MECÁNICO — ver mis asignaciones
@router.get("/mis-asignaciones", response_model=list[AsignacionRead])
def mis_asignaciones(
    usuario: Usuario = Depends(get_current_mecanico),
    db: Session = Depends(get_db),
):
    mecanico = usuario.perfil_mecanico
    return get_asignaciones_de_mecanico(db, mecanico.id)


# ADMIN — rechazar una asignación de su taller
@router.patch("/{asignacion_id}/rechazar", response_model=AsignacionRead)
def rechazar_mi_asignacion(
    asignacion_id: int,
    datos: AsignacionRechazar,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    asignacion = (
        db.query(AsignacionServicio)
        .join(AsignacionServicio.mecanico)
        .filter(
            AsignacionServicio.id == asignacion_id,
            Mecanico.taller_id == taller_id
        )
        .first()
    )
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada o no pertenece a tu taller")

    if asignacion.estado != EstadoAsignacion.pendiente:
        raise HTTPException(
            status_code=400,
            detail=f"No puedes rechazar una asignación en estado '{asignacion.estado.value}'"
        )

    return rechazar_asignacion(db, asignacion, datos.motivo_rechazo)


# MECÁNICO — avanzar estado de su asignación
@router.patch("/{asignacion_id}/estado", response_model=AsignacionRead)
def cambiar_estado_asignacion(
    asignacion_id: int,
    datos: AsignacionEstadoUpdate,
    usuario: Usuario = Depends(get_current_mecanico),
    db: Session = Depends(get_db),
):
    asignacion = get_asignacion_por_id(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    mecanico = usuario.perfil_mecanico
    if asignacion.mecanico_id != mecanico.id:
        raise HTTPException(status_code=403, detail="Esta asignación no es tuya")

    transiciones_validas = {
        EstadoAsignacion.aceptada:    [EstadoAsignacion.en_camino,   EstadoAsignacion.cancelada],
        EstadoAsignacion.en_camino:   [EstadoAsignacion.en_servicio, EstadoAsignacion.cancelada],
        EstadoAsignacion.en_servicio: [EstadoAsignacion.completada],
    }

    estados_permitidos = transiciones_validas.get(asignacion.estado, [])
    if datos.estado not in estados_permitidos:
        permitidos_str = ", ".join(e.value for e in estados_permitidos)
        raise HTTPException(
            status_code=400,
            detail=f"Desde '{asignacion.estado.value}' solo puedes ir a: {permitidos_str}"
        )

    return actualizar_estado_asignacion(db, asignacion, datos)


# COMPARTIDO — obtener una asignación por ID
@router.get("/{asignacion_id}", response_model=AsignacionRead)
def obtener_asignacion(
    asignacion_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    asignacion = (
        db.query(AsignacionServicio)
        .join(AsignacionServicio.mecanico)
        .filter(
            AsignacionServicio.id == asignacion_id,
            Mecanico.taller_id == taller_id
        )
        .first()
    )
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada o no pertenece a tu taller")
    return asignacion