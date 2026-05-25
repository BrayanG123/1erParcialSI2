from sqlalchemy.orm import Session

from app.models.pago import Pago, EstadoPago
from app.models.servicio_realizado import ServicioRealizado
from app.schemas.pago import PagoCreate, PagoMarcarPagado



def crear_pago(db: Session, datos: PagoCreate) -> Pago:
    servicio = db.query(ServicioRealizado).filter(
        ServicioRealizado.id == datos.servicio_id
    ).first()
    if not servicio:
        raise ValueError("ServicioRealizado no encontrado")

    pago = Pago(
        servicio_id=datos.servicio_id,
        monto=servicio.costo_final,    # el monto viene del costo_final del servicio
        metodo=datos.metodo,
        referencia=datos.referencia,
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)
    return pago


def get_pago_por_servicio(db: Session, servicio_id: int) -> Pago | None:
    return db.query(Pago).filter(Pago.servicio_id == servicio_id).first()


def get_pago_por_id(db: Session, pago_id: int) -> Pago | None:
    return db.query(Pago).filter(Pago.id == pago_id).first()


def marcar_pagado(db: Session, pago: Pago, datos: PagoMarcarPagado) -> Pago:
    pago.estado = EstadoPago.pagado
    if datos.referencia:
        pago.referencia = datos.referencia
    db.commit()
    db.refresh(pago)
    return pago