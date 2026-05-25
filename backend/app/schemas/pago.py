from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.pago import EstadoPago, MetodoPago


class PagoCreate(BaseModel):
    servicio_id: int
    metodo:      MetodoPago
    referencia:  Optional[str] = None


class PagoMarcarPagado(BaseModel):
    referencia: Optional[str] = None


class PagoRead(BaseModel):
    id:          int
    servicio_id: int
    monto:       float
    estado:      EstadoPago
    metodo:      Optional[MetodoPago]
    referencia:  Optional[str]
    fecha_pago:  datetime

    model_config = {"from_attributes": True}