from sqlalchemy.orm import Session
from app.models.vehiculo import Vehiculo
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate

def get_vehiculo(db: Session, vehiculo_id: int):
    return db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()

def get_vehiculos_by_cliente(db: Session, cliente_id: int):
    return db.query(Vehiculo).filter(Vehiculo.cliente_id == cliente_id).all()

def get_all_vehiculos(db: Session):
    return db.query(Vehiculo).all()

def crear_vehiculo(db: Session, datos: VehiculoCreate, cliente_id: int):
    nuevo_vehiculo = Vehiculo(
        **datos.model_dump(),
        cliente_id=cliente_id
    )
    db.add(nuevo_vehiculo)
    db.commit()
    db.refresh(nuevo_vehiculo)
    return nuevo_vehiculo

def actualizar_vehiculo(db: Session, vehiculo: Vehiculo, datos: VehiculoUpdate):
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(vehiculo, campo, valor)
    db.commit()
    db.refresh(vehiculo)
    return vehiculo

def eliminar_vehiculo(db: Session, vehiculo: Vehiculo):
    db.delete(vehiculo)
    db.commit()
    return True
