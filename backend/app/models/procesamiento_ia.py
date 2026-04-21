import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base



class EstadoProcesamiento(str, enum.Enum):
    pendiente  = "pendiente"
    completado = "completado"
    error      = "error"


class ProcesamientoIA(Base):
    __tablename__ = "procesamientos_ia"

    id             = Column(Integer, primary_key=True, index=True)
    estado         = Column(
        SAEnum(EstadoProcesamiento, name="estado_procesamiento"),
        default=EstadoProcesamiento.pendiente,
        nullable=False,
    )
    resumen_generado = Column(Text,        nullable=True)   # lo que devolvió la IA
    mensaje_error    = Column(Text,        nullable=True)   # si falló
    modelo_usado     = Column(String(100), nullable=True)   # ej: "gpt-4o-mini"
    fecha_inicio     = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_fin        = Column(DateTime, nullable=True)

    # --- Foreign Key ---
    incidente_id = Column(
        Integer,
        ForeignKey("incidentes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # --- Relación ---
    incidente = relationship("Incidente", back_populates="procesamientos_ia")