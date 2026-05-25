from sqlalchemy.orm import Session
from app.models.taller import Taller
from app.models.usuario import Administrador
from app.schemas.taller import TallerCreate, TallerUpdate, TallerRead

def get_taller_by_admin(db: Session, admin_id: int):
    admin = db.query(Administrador).filter(Administrador.id == admin_id).first()
    return admin.taller if admin else None

def get_all_talleres(db: Session):
    return db.query(Taller).order_by(Taller.id.desc()).all()

def get_taller_por_id(db: Session, taller_id: int) -> Taller | None:
    return db.query(Taller).filter(Taller.id == taller_id).first()

def get_taller_de_admin(db: Session, administrador_id: int) -> Taller | None:
    admin = db.query(Administrador).filter(Administrador.id == administrador_id).first()
    return admin.taller if admin else None

def get_talleres(db: Session, skip: int = 0, limit: int = 100) -> list[Taller]:
    return db.query(Taller).offset(skip).limit(limit).all()


def crear_taller(db: Session, admin_id: int, datos: TallerCreate):
    # 1. Crear el taller
    nuevo_taller = Taller(
        nombre=datos.nombre,
        direccion=datos.direccion,
        telefono=datos.telefono,
        latitud=datos.latitud,
        longitud=datos.longitud,
    )
    db.add(nuevo_taller)
    db.flush() # Para obtener el ID del taller sin hacer commit

    # 2. Sincronizar el perfil Administrador (Administrador.taller_id)
    admin = db.query(Administrador).filter(Administrador.id == admin_id).first()
    if admin:
        admin.taller_id = nuevo_taller.id
    
    db.commit()
    db.refresh(nuevo_taller)
    return nuevo_taller


def actualizar_taller(db: Session, taller: Taller, datos: TallerUpdate) -> Taller:
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(taller, campo, valor)
    db.commit()
    db.refresh(taller)
    return taller


def eliminar_taller(db: Session, taller: Taller) -> None:
    db.delete(taller)
    db.commit()