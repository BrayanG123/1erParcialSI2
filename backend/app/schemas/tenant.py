from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.tenant import PlanTenant



class TenantCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=200, examples=["Auxilio Norte"])
    plan:   PlanTenant = Field(default=PlanTenant.basico)
    activo: bool = Field(default=True)


class TenantUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    plan:   Optional[PlanTenant] = None
    activo: Optional[bool] = None


class TenantRead(BaseModel):
    id:              int
    nombre:          str
    plan:            PlanTenant
    activo:          bool
    fecha_registro:  datetime

    model_config = {"from_attributes": True}


class TenantConEstadisticas(TenantRead):
    """
    TenantRead extendido con conteo de recursos asociados.
    Usado en el endpoint de estadísticas por tenant.
    """
    total_talleres:      int = 0
    total_mecanicos:     int = 0
    total_admins:        int = 0
    total_asignaciones:  int = 0