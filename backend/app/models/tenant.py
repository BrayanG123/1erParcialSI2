import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base



class PlanTenant(str, enum.Enum):
    basico       = "basico"
    profesional  = "profesional"
    enterprise   = "enterprise"


class Tenant(Base):
    __tablename__ = "tenants"

    id               = Column(Integer, primary_key=True, index=True)
    nombre           = Column(String(200), nullable=False, unique=True)
    plan             = Column(SAEnum(PlanTenant, name="plan_tenant"), default=PlanTenant.basico, nullable=False)
    activo           = Column(Boolean, default=True, nullable=False)
    fecha_registro   = Column(DateTime, default=datetime.utcnow, nullable=False)

    # --- Relaciones inversas (para navegar desde Tenant → sus datos) ---
    talleres         = relationship("Taller",             back_populates="tenant")
    mecanicos        = relationship("Mecanico",           back_populates="tenant")
    administradores  = relationship("Administrador",      back_populates="tenant")
    asignaciones     = relationship("AsignacionServicio", back_populates="tenant")
    servicios        = relationship("ServicioRealizado",  back_populates="tenant")
    comisiones       = relationship("Comision",           back_populates="tenant")