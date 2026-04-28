from sqlalchemy.orm import Session
from app.models.taller import Taller
from app.models.usuario import Administrador
from app.schemas.taller import TallerCreate

def get_taller_by_admin(db: Session, admin_id: int):
    return db.query(Taller).filter(Taller.administrador_id == admin_id).first()

def get_all_talleres(db: Session):
    return db.query(Taller).order_by(Taller.id.desc()).all()

def crear_taller(db: Session, admin_id: int, datos: TallerCreate):
    # 1. Crear el taller asignando el admin_id (Taller.administrador_id)
    nuevo_taller = Taller(
        administrador_id=admin_id,
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
