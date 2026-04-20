from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator



class CalificacionCreate(BaseModel):
    servicio_id: int
    puntuacion:  int
    comentario:  Optional[str] = None

    @field_validator("puntuacion")
    @classmethod
    def rango_valido(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("La puntuación debe ser entre 1 y 5")
        return v
    

class CalificacionRead(BaseModel):
    id:          int
    servicio_id: int
    puntuacion:  int
    comentario:  Optional[str]
    fecha:       datetime

    model_config = {"from_attributes": True}