import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base



class Comision(Base):
    __tablename__ = "comisiones"

    id = Column(Integer, primary_key=True, index=True)
    porcentaje = Column(Float, nullable=False)              # ej: 10.0 (= 10%)
    monto = Column(Float, nullable=False)              # calculado al crear
    fecha_emision   = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_pago      = Column(DateTime, nullable=True)              # cuándo el taller pagó

    # --- Foreign Key (1:1 con ServicioRealizado) ---
    servicio_id = Column(
        Integer,
        ForeignKey("servicios_realizados.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    # --- Relación ---
    servicio = relationship("ServicioRealizado", back_populates="comision")