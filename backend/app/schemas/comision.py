from datetime import datetime
from typing import Optional
from pydantic import BaseModel



class ComisionRead(BaseModel):
    id:            int
    servicio_id:   int
    porcentaje:    float
    monto:         float
    fecha_emision: datetime
    fecha_pago:    Optional[datetime]

    model_config = {"from_attributes": True}


