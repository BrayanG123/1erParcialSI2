from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.taller import Taller
from app.models.tenant import Tenant
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
    # 0. Verificar que el nombre del taller no esté ya tomado como tenant
    existe_tenant = db.query(Tenant).filter(Tenant.nombre == datos.nombre).first()
    if existe_tenant:
        raise HTTPException(status_code=400, detail="Ya existe un taller registrado con ese nombre")

    # 1. Crear el Tenant 1:1 asociado al taller
    nuevo_tenant = Tenant(nombre=datos.nombre)
    db.add(nuevo_tenant)
    db.flush()  # Obtener nuevo_tenant.id sin commit

    # 2. Crear el Taller con el tenant_id asignado
    nuevo_taller = Taller(
        nombre=datos.nombre,
        direccion=datos.direccion,
        telefono=datos.telefono,
        latitud=datos.latitud,
        longitud=datos.longitud,
        tenant_id=nuevo_tenant.id,
    )
    db.add(nuevo_taller)
    db.flush()  # Obtener nuevo_taller.id sin commit

    # 3. Sincronizar el perfil Administrador: taller_id y tenant_id
    admin = db.query(Administrador).filter(Administrador.id == admin_id).first()
    if admin:
        admin.taller_id = nuevo_taller.id
        admin.tenant_id = nuevo_tenant.id

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