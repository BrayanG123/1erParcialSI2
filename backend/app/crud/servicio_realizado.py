from sqlalchemy.orm import Session

from app.models.servicio_realizado import ServicioRealizado
from app.models.asignacion_servicio import AsignacionServicio, EstadoAsignacion
from app.schemas.servicio_realizado import ServicioRealizadoCreate



def crear_servicio_realizado(
    db: Session,
    asignacion_id: int,
    datos: ServicioRealizadoCreate,
) -> ServicioRealizado:
    # El servicio hereda el tenant de su asignación (ruta crítica, Fase 7):
    # sin esto, el servicio (y sus pagos/calificaciones vía JOIN) no aparece
    # en los reportes QBE del taller.
    asignacion = (
        db.query(AsignacionServicio)
        .filter(AsignacionServicio.id == asignacion_id)
        .first()
    )

    servicio = ServicioRealizado(
        asignacion_id=asignacion_id,
        tenant_id=asignacion.tenant_id if asignacion else None,
        tipo_servicio=datos.tipo_servicio,
        descripcion_trabajo=datos.descripcion_trabajo,
        costo_final=datos.costo_final,
        observaciones=datos.observaciones,
    )
    db.add(servicio)
    db.commit()
    db.refresh(servicio)
    return servicio



def get_servicio_por_asignacion(
    db: Session, asignacion_id: int
) -> ServicioRealizado | None:
    return (
        db.query(ServicioRealizado)
        .filter(ServicioRealizado.asignacion_id == asignacion_id)
        .first()
    )


def get_servicio_por_id(db: Session, servicio_id: int) -> ServicioRealizado | None:
    return db.query(ServicioRealizado).filter(ServicioRealizado.id == servicio_id).first()



def get_servicios_de_mecanico(db: Session, mecanico_id: int) -> list[ServicioRealizado]:
    """Devuelve todos los servicios realizados por un mecánico (a través de sus asignaciones)."""
    return (
        db.query(ServicioRealizado)
        .join(AsignacionServicio)
        .filter(AsignacionServicio.mecanico_id == mecanico_id)
        .order_by(ServicioRealizado.fecha_realizado.desc())
        .all()
    )