from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario, RolUsuario
from app.models.asignacion_servicio import AsignacionServicio, EstadoAsignacion
from app.models.usuario import Mecanico
from app.models.servicio_realizado import ServicioRealizado as SR
from app.schemas.servicio_realizado import ServicioRealizadoCreate, ServicioRealizadoRead
from app.crud.asignacion_servicio import get_asignacion_por_id, actualizar_estado_asignacion
from app.crud.servicio_realizado import (
    crear_servicio_realizado,
    get_servicio_por_asignacion,
    get_servicio_por_id,
    get_servicios_de_mecanico,
)
from app.schemas.asignacion_servicio import AsignacionEstadoUpdate
from app.core.dependencies import (
    get_current_mecanico,
    get_current_administrador,
    get_current_usuario,
    get_current_cliente
)
from app.services.bitacora import BitacoraService
from app.services.notificacion_service import notificar_cliente_cambio_estado
from app.services.websocket_manager import manager


router = APIRouter(prefix="/servicios-realizados", tags=["Servicios Realizados"])


# ── MECÁNICO — registrar el servicio al completar su asignación ───────────────
@router.post(
    "/asignacion/{asignacion_id}",
    response_model=ServicioRealizadoRead,
    status_code=status.HTTP_201_CREATED,
)
async def registrar_servicio(
    asignacion_id: int,
    datos: ServicioRealizadoCreate,
    usuario: Usuario = Depends(get_current_mecanico),
    db: Session = Depends(get_db),
):
    asignacion = get_asignacion_por_id(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    mecanico = usuario.perfil_mecanico
    if asignacion.mecanico_id != mecanico.id:
        raise HTTPException(status_code=403, detail="Esta asignación no es tuya")

    if asignacion.estado != EstadoAsignacion.en_atencion:
        raise HTTPException(
            status_code=400,
            detail=f"Solo puedes registrar el servicio cuando estás 'en_atencion'. "
                   f"Estado actual: '{asignacion.estado.value}'"
        )

    existente = get_servicio_por_asignacion(db, asignacion_id)
    if existente:
        raise HTTPException(status_code=400, detail="Esta asignación ya tiene un servicio registrado")

    servicio = crear_servicio_realizado(db, asignacion_id, datos)

    actualizar_estado_asignacion(
        db, asignacion, AsignacionEstadoUpdate(estado=EstadoAsignacion.finalizado)
    )

    # ── Notificar al cliente: servicio finalizado, califica y paga ───────
    # (Fase 7 de la ruta crítica — este es el camino real con el que el
    #  mecánico cierra el servicio, por eso la notificación va AQUÍ)
    try:
        incidente = asignacion.incidente
        if incidente and incidente.cliente:
            notificar_cliente_cambio_estado(
                db=db,
                cliente_usuario_id=incidente.cliente.usuario_id,
                incidente_id=incidente.id,
                mensaje=f"Tu servicio fue completado (Bs. {servicio.costo_final:.2f}). "
                        "Por favor califícalo y realiza el pago desde la app.",
                tipo="estado_asignacion",
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error enviando push de finalizado: {e}")

    # ── Emitir el cierre por WebSocket (el tracking del cliente se entera) ─
    try:
        await manager.broadcast(
            incidente_id=asignacion.incidente_id,
            mensaje={
                "tipo": "cambio_estado",
                "estado": EstadoAsignacion.finalizado.value,
                "asignacion_id": asignacion.id,
                "incidente_id": asignacion.incidente_id,
                "mecanico": None,
            },
        )
        # El servicio terminó: liberar la posición del mecánico en memoria
        manager.limpiar_posicion(asignacion.incidente_id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error emitiendo cierre por WebSocket: {e}")

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


# ── CLIENTE — ver el servicio de su propia asignación ────────────────────────
@router.get("/mi-asignacion/{asignacion_id}", response_model=ServicioRealizadoRead)
def mi_servicio_de_asignacion(
    asignacion_id: int,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """El cliente consulta el servicio realizado en su asignación."""
    from app.crud.asignacion_servicio import get_asignacion_por_id
    asignacion = get_asignacion_por_id(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    # Verificar que el incidente de esa asignación pertenece al cliente
    incidente = asignacion.incidente
    if incidente.cliente.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    servicio = get_servicio_por_asignacion(db, asignacion_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Aún no hay servicio registrado")
    return servicio



# ── ADMIN — ver servicio de una asignación específica ────────────────────────
@router.get("/asignacion/{asignacion_id}", response_model=ServicioRealizadoRead)
def servicio_de_asignacion(
    asignacion_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    # Verificar que la asignación pertenece al taller del admin
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

    servicio = get_servicio_por_asignacion(db, asignacion_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Esta asignación no tiene servicio registrado aún")
    return servicio


# ── ADMIN — ver todos los servicios realizados de SU taller ──────────────────
@router.get("/", response_model=list[ServicioRealizadoRead])
def listar_servicios(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    return (
        db.query(SR)
        .join(SR.asignacion)                  # SR → AsignacionServicio
        .join(AsignacionServicio.mecanico)    # AsignacionServicio → Mecanico
        .filter(Mecanico.taller_id == taller_id)
        .order_by(SR.fecha_realizado.desc())
        .all()
    )