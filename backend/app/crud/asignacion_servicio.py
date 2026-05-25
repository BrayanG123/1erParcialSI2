from datetime import datetime
from sqlalchemy.orm import Session

from app.models.asignacion_servicio import AsignacionServicio, EstadoAsignacion
from app.schemas.asignacion_servicio import AsignacionCreate, AsignacionEstadoUpdate
from app.models.historial_estado import HistorialEstado


def crear_asignacion(db: Session, datos: AsignacionCreate) -> AsignacionServicio:
    asignacion = AsignacionServicio(
        incidente_id=datos.incidente_id,
        mecanico_id=datos.mecanico_id,
        costo_estimado=datos.costo_estimado,
        distancia_km=datos.distancia_km,
        tiempo_estimado=datos.tiempo_estimado,
    )
    db.add(asignacion)
    db.commit()
    db.refresh(asignacion)
    return asignacion



def get_asignacion_por_id(db: Session, asignacion_id: int) -> AsignacionServicio | None:
    return db.query(AsignacionServicio).filter(AsignacionServicio.id == asignacion_id).first()



def get_asignacion_por_incidente(db: Session, incidente_id: int) -> AsignacionServicio | None:
    return (
        db.query(AsignacionServicio)
        .filter(AsignacionServicio.incidente_id == incidente_id)
        .first()
    )


def get_asignaciones_de_mecanico(db: Session, mecanico_id: int) -> list[AsignacionServicio]:
    return (
        db.query(AsignacionServicio)
        .filter(AsignacionServicio.mecanico_id == mecanico_id)
        .order_by(AsignacionServicio.fecha_creacion.desc())
        .all()
    )


def aceptar_asignacion(db: Session, asignacion: AsignacionServicio) -> AsignacionServicio:
    asignacion.estado = EstadoAsignacion.aceptada
    asignacion.fecha_respuesta = datetime.utcnow()
    db.commit()
    db.refresh(asignacion)
    return asignacion


def rechazar_asignacion(
    db: Session, asignacion: AsignacionServicio, motivo: str
) -> AsignacionServicio:
    asignacion.estado = EstadoAsignacion.rechazada
    asignacion.fecha_respuesta = datetime.utcnow()
    asignacion.motivo_rechazo = motivo
    db.commit()
    db.refresh(asignacion)
    return asignacion


def actualizar_estado_asignacion(
    db: Session, 
    asignacion: AsignacionServicio, 
    datos: AsignacionEstadoUpdate
) -> AsignacionServicio:
    # Registrar el cambio en el historial ANTES de actualizar
    historial = HistorialEstado(
        asignacion_id=asignacion.id,
        estado_anterior=asignacion.estado.value if asignacion.estado else None,
        estado_actual=datos.estado.value,
    )
    db.add(historial)
    
    asignacion.estado = datos.estado
    db.commit()
    db.refresh(asignacion)
    return asignacion


def get_todas_las_asignaciones(db: Session) -> list[AsignacionServicio]:
    return (
        db.query(AsignacionServicio)
        .order_by(AsignacionServicio.fecha_creacion.desc())
        .all()
    )