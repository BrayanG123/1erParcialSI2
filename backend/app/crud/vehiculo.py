import os
import shutil
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.vehiculo import Vehiculo
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate


def get_vehiculos_de_cliente(db: Session, cliente_id: int) -> List[Vehiculo]:
    return (
        db.query(Vehiculo)
        .filter(Vehiculo.cliente_id == cliente_id)
        .order_by(Vehiculo.id.desc())
        .all()
    )


def get_vehiculo_por_id(db: Session, vehiculo_id: int) -> Optional[Vehiculo]:
    return db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()


def crear_vehiculo(db: Session, cliente_id: int, datos: VehiculoCreate) -> Vehiculo:
    vehiculo = Vehiculo(
        cliente_id=cliente_id,
        placa=datos.placa,
        modelo=datos.modelo,
        color=datos.color,
        tipo_seguro=datos.tipo_seguro,
    )
    db.add(vehiculo)
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


def actualizar_vehiculo(db: Session, vehiculo: Vehiculo, datos: VehiculoUpdate) -> Vehiculo:
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(vehiculo, campo, valor)
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


def guardar_foto_vehiculo(
    db: Session, vehiculo: Vehiculo, archivo: UploadFile
) -> Vehiculo:
    directorio = "media/vehiculos"
    os.makedirs(directorio, exist_ok=True)
    ruta = f"{directorio}/vehiculo_{vehiculo.id}{os.path.splitext(archivo.filename)[1]}"
    with open(ruta, "wb") as f:
        shutil.copyfileobj(archivo.file, f)
    vehiculo.foto_vehiculo = ruta
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


def eliminar_vehiculo(db: Session, vehiculo: Vehiculo) -> None:
    db.delete(vehiculo)
    db.commit()