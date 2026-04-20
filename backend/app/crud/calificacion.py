from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.calificacion import Calificacion
from app.models.servicio_realizado import ServicioRealizado
from app.models.asignacion_servicio import AsignacionServicio
from app.models.usuario import Mecanico
from app.models.taller import Taller
from app.schemas.calificacion import CalificacionCreate



def crear_calificacion(db: Session, datos: CalificacionCreate) -> Calificacion:
    calificacion = Calificacion(
        servicio_id=datos.servicio_id,
        puntuacion=datos.puntuacion,
        comentario=datos.comentario,
    )
    db.add(calificacion)
    db.flush()   # genera el id sin hacer commit todavía

    # Recalcular promedio del mecánico
    _recalcular_promedio_mecanico(db, datos.servicio_id)

    # Recalcular promedio del taller
    _recalcular_promedio_taller(db, datos.servicio_id)

    db.commit()
    db.refresh(calificacion)
    return calificacion


def get_calificacion_por_servicio(db: Session, servicio_id: int) -> Calificacion | None:
    return (
        db.query(Calificacion)
        .filter(Calificacion.servicio_id == servicio_id)
        .first()
    )



def get_calificaciones_de_mecanico(
    db: Session, mecanico_id: int
) -> list[Calificacion]:
    return (
        db.query(Calificacion)
        .join(ServicioRealizado)
        .join(AsignacionServicio)
        .filter(AsignacionServicio.mecanico_id == mecanico_id)
        .order_by(Calificacion.fecha.desc())
        .all()
    )



# ── helpers privados ──────────────────────────────────────────────────────────
def _recalcular_promedio_mecanico(db: Session, servicio_id: int) -> None:
    """Recalcula el promedio de calificaciones del mecánico y lo guarda."""
    # Obtener el mecanico_id desde el servicio
    asignacion = (
        db.query(AsignacionServicio)
        .join(ServicioRealizado)
        .filter(ServicioRealizado.id == servicio_id)
        .first()
    )
    if not asignacion or not asignacion.mecanico_id:
        return

    promedio = (
        db.query(func.avg(Calificacion.puntuacion))
        .join(ServicioRealizado)
        .join(AsignacionServicio)
        .filter(AsignacionServicio.mecanico_id == asignacion.mecanico_id)
        .scalar()
    )

    mecanico = db.query(Mecanico).filter(Mecanico.id == asignacion.mecanico_id).first()
    if mecanico:
        mecanico.calificacion_promedio = round(float(promedio), 2)




def _recalcular_promedio_taller(db: Session, servicio_id: int) -> None:
    """Recalcula el promedio de calificaciones del taller y lo guarda."""
    asignacion = (
        db.query(AsignacionServicio)
        .join(ServicioRealizado)
        .filter(ServicioRealizado.id == servicio_id)
        .first()
    )
    if not asignacion or not asignacion.mecanico_id:
        return

    mecanico = db.query(Mecanico).filter(Mecanico.id == asignacion.mecanico_id).first()
    if not mecanico or not mecanico.taller_id:
        return

    promedio = (
        db.query(func.avg(Calificacion.puntuacion))
        .join(ServicioRealizado)
        .join(AsignacionServicio)
        .join(Mecanico)
        .filter(Mecanico.taller_id == mecanico.taller_id)
        .scalar()
    )

    taller = db.query(Taller).filter(Taller.id == mecanico.taller_id).first()
    if taller:
        taller.calificacion_promedio = round(float(promedio), 2)