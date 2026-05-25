from typing import Optional
from pydantic import BaseModel, field_validator



class CategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    prioridad: int = 1

    @field_validator("prioridad")
    @classmethod
    def prioridad_valida(cls, v: int) -> int:
        if v not in (1, 2, 3):
            raise ValueError("La prioridad debe ser 1 (baja), 2 (media) o 3 (alta)")
        return v
    
class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    prioridad: Optional[int] = None

    @field_validator("prioridad")
    @classmethod
    def prioridad_valida(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in (1, 2, 3):
            raise ValueError("La prioridad debe ser 1 (baja), 2 (media) o 3 (alta)")
        return v
    

class CategoriaRead(CategoriaBase):
    id: int

    model_config = {"from_attributes": True}