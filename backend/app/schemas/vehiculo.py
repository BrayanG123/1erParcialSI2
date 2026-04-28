from typing import Optional
from pydantic import BaseModel

class VehiculoBase(BaseModel):
    placa: str
    modelo: str
    color: str
    foto_vehiculo: Optional[str] = None
    tipo_seguro: Optional[str] = None

class VehiculoCreate(VehiculoBase):
    pass

class VehiculoUpdate(BaseModel):
    placa: Optional[str] = None
    modelo: Optional[str] = None
    color: Optional[str] = None
    foto_vehiculo: Optional[str] = None
    tipo_seguro: Optional[str] = None

class VehiculoRead(VehiculoBase):
    id: int
    cliente_id: int

    model_config = {"from_attributes": True}
