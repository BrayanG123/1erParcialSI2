from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class ServicioRealizadoCreate(BaseModel):
    tipo_servicio:       str
    descripcion_trabajo: str
    costo_final:         float
    observaciones:       Optional[str] = None

    @field_validator("costo_final")
    @classmethod
    def costo_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("El costo final debe ser mayor a 0")
        return v

    @field_validator("tipo_servicio", "descripcion_trabajo")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Este campo no puede estar vacío")
        return v
    

class ServicioRealizadoRead(BaseModel):
    id:                  int
    asignacion_id:       int
    tipo_servicio:       str
    descripcion_trabajo: str
    costo_final:         float
    observaciones:       Optional[str]
    fecha_realizado:     datetime

    model_config = {"from_attributes": True}