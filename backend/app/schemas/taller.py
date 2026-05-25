from typing import Optional
from pydantic import BaseModel



class TallerBase(BaseModel):
    nombre: str
    direccion: str
    telefono: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None


class TallerCreate(TallerBase):
    pass


class TallerUpdate(BaseModel):
    nombre: Optional[str] = None
    direccion: Optional[str] = None
    telefono:  Optional[str]   = None
    latitud:   Optional[float] = None
    longitud:  Optional[float] = None



class TallerRead(TallerBase):
    id: int
    calificacion_promedio: Optional[float] = 0.0

    model_config = {"from_attributes": True}

    model_config = {"from_attributes": True}