from typing import Optional
from pydantic import BaseModel, field_validator


class VehiculoBase(BaseModel):
    placa: str
    modelo: str
    color: str
    foto_vehiculo: Optional[str] = None
    tipo_seguro: Optional[str] = None


class VehiculoCreate(VehiculoBase):
    @field_validator("placa", "modelo", "color")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v.strip().upper() if len(v) <= 20 else v.strip()


class VehiculoUpdate(BaseModel):
    modelo: Optional[str] = None
    color: Optional[str] = None
    tipo_seguro: Optional[str] = None


class VehiculoRead(VehiculoBase):
    id: int
    cliente_id: int
    foto_vehiculo: Optional[str] = None

    model_config = {"from_attributes": True}