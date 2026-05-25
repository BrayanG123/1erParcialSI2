from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import Base



class HistorialEstado(Base):
    __tablename__ = "historial_estados"

    id              = Column(Integer, primary_key=True, index=True)
    estado_anterior = Column(String(50), nullable=True)    # None si es el primer estado
    estado_actual   = Column(String(50), nullable=False)
    observacion     = Column(Text, nullable=True)
    fecha_cambio    = Column(DateTime, default=datetime.utcnow, nullable=False)

    # --- Foreign Key ---
    asignacion_id = Column(
        Integer,
        ForeignKey("asignaciones_servicio.id", ondelete="CASCADE"),
        nullable=False,
    )

    # --- Relación ---
    asignacion = relationship("AsignacionServicio", back_populates="historial")