from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BitacoraRead(BaseModel):
    id: int
    usuario_id: Optional[int] = None
    accion: str
    descripcion: Optional[str] = None
    ip_address: Optional[str] = None
    entidad_afectada: Optional[str] = None
    fecha: datetime

    model_config = { "from_attributes": True }