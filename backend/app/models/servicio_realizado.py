from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import Base


class ServicioRealizado(Base):
    __tablename__ = "servicios_realizados"

    id                   = Column(Integer, primary_key=True, index=True)
    tipo_servicio        = Column(String(200), nullable=False)   # ej: "Cambio de llanta"
    descripcion_trabajo  = Column(Text,        nullable=False)   # detalle de lo que se hizo
    costo_final          = Column(Float,       nullable=False)   # costo real cobrado
    observaciones        = Column(Text,        nullable=True)    # notas adicionales del mecánico
    fecha_realizado      = Column(DateTime, default=datetime.utcnow, nullable=False)


    # --- Foreign Key  ---
    # (1:1 con AsignacionServicio) 
    asignacion_id = Column(
        Integer,
        ForeignKey("asignaciones_servicio.id", ondelete="CASCADE"),
        unique=True,    # garantiza la relación 1:1
        nullable=False
    )

    # ---  FK hacia tenants ---
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # --- Relaciones ---
    asignacion = relationship("AsignacionServicio", back_populates="servicio_realizado")
    tenant = relationship("Tenant",             back_populates="servicios")
    pago       = relationship("Pago",     back_populates="servicio", uselist=False)
    comision   = relationship("Comision", back_populates="servicio", uselist=False)
    calificacion = relationship("Calificacion",  back_populates="servicio", uselist=False)