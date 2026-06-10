from typing import Optional
from sqlalchemy.orm import Session
from app.models.taller import Taller
from app.models.usuario import Administrador
from app.models.tenant import Tenant
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


def _nombre_tenant_unico(db: Session, base_nombre: str) -> str:
    """
    Tenant.nombre es UNIQUE. Si ya existe un tenant con ese nombre
    (dos talleres distintos con el mismo nombre), devolvemos una
    variante numerada para no romper el INSERT con un IntegrityError.
    Ej: "Auxilio Norte" -> "Auxilio Norte (2)"
    """
    nombre = base_nombre
    contador = 1
    while db.query(Tenant).filter(Tenant.nombre == nombre).first():
        contador += 1
        nombre = f"{base_nombre} ({contador})"
    return nombre


def crear_taller(db: Session, admin_id: int, datos: TallerCreate):
    # 1. Crear el Tenant (organización) al que pertenecerá este taller.
    #    En el onboarding, cada admin que registra su taller genera su
    #    propio tenant. Es el momento en que "nace" el tenant en el sistema.
    nuevo_tenant = Tenant(
        nombre=_nombre_tenant_unico(db, datos.nombre),
        activo=True,
    )
    db.add(nuevo_tenant)
    db.flush()  # obtener nuevo_tenant.id sin hacer commit

    # 2. Crear el taller, ya vinculado al tenant
    nuevo_taller = Taller(
        nombre=datos.nombre,
        direccion=datos.direccion,
        telefono=datos.telefono,
        latitud=datos.latitud,
        longitud=datos.longitud,
        tenant_id=nuevo_tenant.id,
    )
    db.add(nuevo_taller)
    db.flush() # Para obtener el ID del taller sin hacer commit

    # 3. Sincronizar el perfil Administrador (taller_id Y tenant_id)
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