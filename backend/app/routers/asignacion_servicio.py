from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.models.asignacion_servicio import EstadoAsignacion
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
    get_todas_las_asignaciones,
)

from app.crud.incidente import get_incidente_por_id, marcar_no_disponible

from app.core.dependencies import (
    get_current_administrador,
    get_current_mecanico,
)
from app.services.bitacora import BitacoraService



router = APIRouter(prefix="/asignaciones", tags=["Asignaciones de Servicio"])



# ADMIN — crear una asignación (asignar mecánico a un incidente)
@router.post("/", response_model=AsignacionRead, status_code=status.HTTP_201_CREATED)
def crear_nueva_asignacion(
    datos: AsignacionCreate,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """El admin asigna un mecánico a un incidente pendiente."""
    # Verificar que el incidente no tenga ya una asignación activa
    existente = get_asignacion_por_incidente(db, datos.incidente_id)
    if existente and existente.estado not in (
        EstadoAsignacion.rechazada,
        EstadoAsignacion.cancelada,
    ):
        raise HTTPException(
            status_code=400,
            detail="El incidente ya tiene una asignación activa"
        )

    asignacion = crear_asignacion(db, datos)

    incidente = get_incidente_por_id(db, datos.incidente_id)
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    if incidente.estado != EstadoIncidente.disponible:   # necesitas importar EstadoIncidente
        raise HTTPException(status_code=400, detail="El incidente no está disponible")
    
    marcar_no_disponible(db, incidente)

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="CREAR_ASIGNACION",
        descripcion=f"Asignación #{asignacion.id} creada para incidente #{datos.incidente_id}",
    )
    return asignacion



# ADMIN — listar todas las asignaciones
@router.get("/", response_model=list[AsignacionRead])
def listar_asignaciones(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    return get_todas_las_asignaciones(db)


# MECÁNICO — ver mis asignaciones
@router.get("/mis-asignaciones", response_model=list[AsignacionRead])
def mis_asignaciones(
    usuario: Usuario = Depends(get_current_mecanico),
    db: Session = Depends(get_db),
):
    """El mecánico ve todas las asignaciones que le han hecho."""
    mecanico = usuario.perfil_mecanico
    return get_asignaciones_de_mecanico(db, mecanico.id)



# ADMINISTRADOR — rechazar una asignación
@router.patch("/{asignacion_id}/rechazar", response_model=AsignacionRead)
def rechazar_mi_asignacion(
    asignacion_id: int,
    datos: AsignacionRechazar,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    asignacion = get_asignacion_por_id(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    administrador = usuario.perfil_administrador
    if asignacion.administrador_id != administrador.id:
        raise HTTPException(status_code=403, detail="Esta asignación no es tuya")

    if asignacion.estado != EstadoAsignacion.pendiente:
        raise HTTPException(
            status_code=400,
            detail=f"No puedes rechazar una asignación en estado '{asignacion.estado.value}'"
        )

    return rechazar_asignacion(db, asignacion, datos.motivo_rechazo)



# MECÁNICO — avanzar el estado de su asignacion (el mecanico sí puede editar los estados de su asignacion)
@router.patch("/{asignacion_id}/estado", response_model=AsignacionRead)
def cambiar_estado_asignacion(
    asignacion_id: int,
    datos: AsignacionEstadoUpdate,
    usuario: Usuario = Depends(get_current_mecanico),
    db: Session = Depends(get_db),
):
    """
    El mecánico avanza el estado de su asignación:
    aceptada → en_camino → en_servicio → completada
    """
    asignacion = get_asignacion_por_id(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    mecanico = usuario.perfil_mecanico
    if asignacion.mecanico_id != mecanico.id:
        raise HTTPException(status_code=403, detail="Esta asignación no es tuya")

    # Transiciones válidas
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



# COMPARTIDO — ver una asignación por ID
@router.get("/{asignacion_id}", response_model=AsignacionRead)
def obtener_asignacion(
    asignacion_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    asignacion = get_asignacion_por_id(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return asignacion