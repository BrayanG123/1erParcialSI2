import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base



class TipoEvidencia(str, enum.Enum):
    foto  = "foto"
    audio = "audio"



class Evidencia(Base):
    __tablename__ = "evidencias"

    id            = Column(Integer, primary_key=True, index=True)
    tipo          = Column(SAEnum(TipoEvidencia, name="tipo_evidencia"), nullable=False)
    url_archivo   = Column(String(500), nullable=False)   # ruta o URL del archivo
    fecha_subida  = Column(DateTime, default=datetime.utcnow, nullable=False)
    procesado_ia  = Column(Integer,  default=0, nullable=False)   # 0=no, 1=sí

    # --- Foreign Key ---
    incidente_id = Column(
        Integer,
        ForeignKey("incidentes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # --- Relación ---
    incidente = relationship("Incidente", back_populates="evidencias")


