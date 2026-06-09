from sqlalchemy.orm import Session

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


def get_incidentes_disponibles(db: Session) -> list[Incidente]:
    """Incidentes visibles para los administradores de taller (como pasajeros esperando en Uber)."""
    return (
        db.query(Incidente)
        .filter(Incidente.estado == EstadoIncidente.disponible)
        .order_by(Incidente.fecha_hora.asc())
        .all()
    )


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