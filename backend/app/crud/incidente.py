from sqlalchemy.orm import Session

from app.models.historial_estado import HistorialEstado
from app.models.incidente import Incidente, EstadoIncidente
from app.schemas.incidente import IncidenteCreate, IncidenteUpdate


def crear_incidente(db: Session, cliente_id: int, datos: IncidenteCreate) -> Incidente:
    """Crea un nuevo incidente reportado por un cliente."""
    incidente = Incidente(
        cliente_id=cliente_id,
        vehiculo_id=datos.vehiculo_id,
        categoria_id=datos.categoria_id,
        descripcion=datos.descripcion,
        latitud=datos.latitud,
        longitud=datos.longitud,
    )
    db.add(incidente)
    db.flush()

    # Primer registro del historial (ruta crítica, Fase 1):
    # el incidente nace en estado 'pendiente' (aún sin taller)
    db.add(HistorialEstado(
        incidente_id=incidente.id,
        estado_anterior=None,
        estado_actual="pendiente",
        observacion="Incidente reportado por el cliente",
    ))

    db.commit()
    db.refresh(incidente)
    return incidente


def get_incidente_por_id(db: Session, incidente_id: int) -> Incidente | None:
    return db.query(Incidente).filter(Incidente.id == incidente_id).first()


def get_incidentes_de_cliente(db: Session, cliente_id: int) -> list[Incidente]:
    return (
        db.query(Incidente)
        .filter(Incidente.cliente_id == cliente_id)
        .order_by(Incidente.fecha_hora.desc())
        .all()
    )


def get_incidentes_disponibles(
    db: Session,
    excluir_rechazados_de_tenant: int | None = None,
) -> list[Incidente]:
    """
    Incidentes visibles para los administradores de taller.

    Si se pasa un tenant, se EXCLUYEN los incidentes que ese taller ya
    rechazó (quedan disponibles para los demás talleres — la política de
    "considerar al siguiente taller" de la ruta crítica).
    """
    from app.models.asignacion_servicio import AsignacionServicio, EstadoAsignacion

    q = db.query(Incidente).filter(Incidente.estado == EstadoIncidente.disponible)

    if excluir_rechazados_de_tenant:
        rechazados = (
            db.query(AsignacionServicio.incidente_id)
            .filter(
                AsignacionServicio.tenant_id == excluir_rechazados_de_tenant,
                AsignacionServicio.estado == EstadoAsignacion.rechazada,
            )
        )
        q = q.filter(~Incidente.id.in_(rechazados))

    return q.order_by(Incidente.fecha_hora.asc()).all()


def actualizar_incidente(db: Session, incidente: Incidente, datos: IncidenteUpdate) -> Incidente:
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(incidente, campo, valor)
    db.commit()
    db.refresh(incidente)
    return incidente


def marcar_no_disponible(db: Session, incidente: Incidente) -> Incidente:
    """Llamado automáticamente cuando un admin acepta el incidente y crea una AsignacionServicio."""
    incidente.estado = EstadoIncidente.no_disponible
    db.commit()
    db.refresh(incidente)
    return incidente

# def cancelar_incidente(db: Session, incidente: Incidente) -> Incidente:
#     """Llamado cuando el cliente cancela su propio incidente."""
#     incidente.estado = EstadoIncidente.cancelado
#     db.commit()
#     db.refresh(incidente)
#     return incidente