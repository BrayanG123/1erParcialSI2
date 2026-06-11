from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.asignacion_servicio import EstadoAsignacion


# ── Creación (admin asigna mecánico a un incidente) 
class AsignacionCreate(BaseModel):
    incidente_id: int
    mecanico_id: Optional[int] = None   # opcional: el admin puede aceptar sin asignar mecánico aún
    costo_estimado: Optional[float] = None
    distancia_km: Optional[float] = None
    tiempo_estimado: Optional[int] = None


# ── Asignar mecánico a una asignación ya aceptada
class AsignacionAsignarMecanico(BaseModel):
    mecanico_id: int


# ── Rechazo (mecánico rechaza con motivo)
class AsignacionRechazar(BaseModel):
    motivo_rechazo: str


# ── Actualización de estado (mecánico avanza el estado) 
class AsignacionEstadoUpdate(BaseModel):
    estado: EstadoAsignacion


# ── Resúmenes anidados (para que el front identifique la asignación)
class IncidenteResumen(BaseModel):
    id: int
    descripcion: str
    fecha_hora: datetime
    latitud: Optional[float] = None    # ubicación del cliente (para el mapa del mecánico)
    longitud: Optional[float] = None

    model_config = {"from_attributes": True}


class UsuarioResumen(BaseModel):
    nombre: str
    apellido: str

    model_config = {"from_attributes": True}


class MecanicoResumen(BaseModel):
    id: int
    usuario: Optional[UsuarioResumen] = None

    model_config = {"from_attributes": True}


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
    incidente:       Optional[IncidenteResumen] = None
    mecanico:        Optional[MecanicoResumen] = None

    model_config = {"from_attributes": True}