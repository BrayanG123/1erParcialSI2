from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.asignacion_servicio import EstadoAsignacion


# ── Creación (admin asigna mecánico a un incidente) 
class AsignacionCreate(BaseModel):
    incidente_id: int  
    mecanico_id: int
    costo_estimado: Optional[float] = None
    distancia_km: Optional[float] = None
    tiempo_estimado: Optional[int] = None


# ── Rechazo (mecánico rechaza con motivo) 
class AsignacionRechazar(BaseModel):
    motivo_rechazo: str


# ── Actualización de estado (mecánico avanza el estado) 
class AsignacionEstadoUpdate(BaseModel):
    estado: EstadoAsignacion


# ── Lectura
class AsignacionRead(BaseModel):
    id:              int
    incidente_id:    int   
    mecanico_id:     Optional[int]
    costo_estimado:  Optional[float]
    distancia_km:    Optional[float]
    tiempo_estimado: Optional[int]
    estado:          EstadoAsignacion
    fecha_creacion:  datetime
    fecha_respuesta: Optional[datetime]
    motivo_rechazo:  Optional[str]

    model_config = {"from_attributes": True}