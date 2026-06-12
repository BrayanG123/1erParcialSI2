from sqlalchemy.orm import Session

from app.models.comision import Comision
from app.models.servicio_realizado import ServicioRealizado
# from app.schemas.comision import ComisionEstadoUpdate


# Porcentaje fijo de comisión de la plataforma
PORCENTAJE_COMISION = 10.0   # 10%


def crear_comision(db: Session, servicio_id: int) -> Comision:
    servicio = db.query(ServicioRealizado).filter(
        ServicioRealizado.id == servicio_id
    ).first()
    if not servicio:
        raise ValueError("ServicioRealizado no encontrado")

    monto = round(servicio.costo_final * PORCENTAJE_COMISION / 100, 2)

    comision = Comision(
        servicio_id=servicio_id,
        tenant_id=servicio.tenant_id,   # hereda el tenant del servicio
        porcentaje=PORCENTAJE_COMISION,
        monto=monto,
    )
    db.add(comision)
    db.commit()
    db.refresh(comision)
    return comision


def get_comision_por_servicio(db: Session, servicio_id: int) -> Comision | None:
    return db.query(Comision).filter(Comision.servicio_id == servicio_id).first()


def get_comision_por_id(db: Session, comision_id: int) -> Comision | None:
    return db.query(Comision).filter(Comision.id == comision_id).first()


# def actualizar_estado_comision(
#     db: Session, comision: Comision, datos: ComisionEstadoUpdate
# ) -> Comision:
#     comision.estado = datos.estado
#     if datos.observaciones:
#         comision.observaciones = datos.observaciones
#     if datos.fecha_pago:
#         comision.fecha_pago = datos.fecha_pago
#     db.commit()
#     db.refresh(comision)
#     return comision