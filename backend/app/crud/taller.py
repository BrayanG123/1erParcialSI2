from sqlalchemy.orm import Session

from app.models.taller import Taller
from app.schemas.taller import TallerCreate, TallerUpdate


def crear_taller(db: Session, datos: TallerCreate, administrador_id: int) -> Taller:
    taller = Taller(
        administrador_id=administrador_id,
        nombre=datos.nombre,
        direccion=datos.direccion,
        telefono=datos.telefono,
        latitud=datos.latitud,
        longitud=datos.longitud,
    )
    db.add(taller)
    db.commit()
    db.refresh(taller)
    return taller


def get_taller_por_id(db: Session, taller_id: int) -> Taller | None:
    return db.query(Taller).filter(Taller.id == taller_id).first()


def get_taller_de_admin(db: Session, administrador_id: int) -> Taller | None:
    return db.query(Taller).filter(Taller.administrador_id == administrador_id).first()


def get_talleres(db: Session, skip: int = 0, limit: int = 100) -> list[Taller]:
    return db.query(Taller).offset(skip).limit(limit).all()


def actualizar_taller(db: Session, taller: Taller, datos: TallerUpdate) -> Taller:
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(taller, campo, valor)
    db.commit()
    db.refresh(taller)
    return taller


def eliminar_taller(db: Session, taller: Taller) -> None:
    db.delete(taller)
    db.commit()
