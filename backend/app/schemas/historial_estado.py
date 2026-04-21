from datetime import datetime
from typing import Optional
from pydantic import BaseModel



class HistorialEstadoRead(BaseModel):
    id:              int
    asignacion_id:   int
    estado_anterior: Optional[str]
    estado_actual:   str
    observacion:     Optional[str]
    fecha_cambio:    datetime

    model_config = {"from_attributes": True}