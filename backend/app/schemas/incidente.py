from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from app.models.incidente import EstadoIncidente


# ── Base ──────────────────────────────────────────────────────────────────────
class IncidenteBase(BaseModel):
    descripcion: str
    latitud: float
    longitud: float
    vehiculo_id: Optional[int] = None
    categoria_id: Optional[int] = None


# ── Create (lo que envía el cliente al reportar) ───────────────────────────────
class IncidenteCreate(IncidenteBase):
    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v


# Solo admin/IA pueden modificar un incidente (estado y resumen generado por IA)
class IncidenteUpdate(BaseModel):
    estado: Optional[EstadoIncidente] = None
    resumen_ia: Optional[str] = None
    categoria_id: Optional[int] = None


# ── Read (lo que devuelve la API) ─────────────────────────────────────────────
class IncidenteRead(IncidenteBase):
    id: int
    fecha_hora: datetime
    estado: EstadoIncidente
    resumen_ia: Optional[str] = None
    foto_incidente: Optional[str] = None
    audio_descripcion: Optional[str] = None
    cliente_id: int

    model_config = {"from_attributes": True}
