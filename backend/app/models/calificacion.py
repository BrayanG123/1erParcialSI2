from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base



class Calificacion(Base):
    __tablename__ = "calificaciones"

    __table_args__ = (
        CheckConstraint("puntuacion >= 1 AND puntuacion <= 5", name="ck_puntuacion_rango"),
    )

    id = Column(Integer, primary_key=True, index=True)
    puntuacion  = Column(Integer, nullable=False) # 1 a 5
    comentario  = Column(Text,    nullable=True)
    fecha       = Column(DateTime, default=datetime.utcnow, nullable=False)

    # --- Foreign Key (1:1 con ServicioRealizado) ---
    servicio_id = Column(
        Integer,
        ForeignKey("servicios_realizados.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # --- Relación ---
    servicio = relationship("ServicioRealizado", back_populates="calificacion")