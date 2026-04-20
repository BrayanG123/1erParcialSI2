import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base


class EstadoAsignacion(str, enum.Enum):
    pendiente   = "pendiente"
    aceptada    = "aceptada"
    rechazada   = "rechazada"
    en_camino   = "en_camino"
    en_servicio = "en_servicio"
    completada  = "completada"
    cancelada   = "cancelada"


class AsignacionServicio(Base):
    __tablename__ = "asignaciones_servicio"

    id = Column(Integer, primary_key=True, index=True)
    costo_estimado = Column(Float, nullable=True)
    distancia_km = Column(Float, nullable=True)
    tiempo_estimado = Column(Integer, nullable=True)
    estado = Column(
        SAEnum(EstadoAsignacion, name="estado_asignacion"),
        default=EstadoAsignacion.pendiente,
        nullable=False
    )
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_respuesta = Column(DateTime, nullable=True)
    motivo_rechazo = Column(Text, nullable=True)


    # --- Foreign Keys ---
    incidente_id = Column(
        Integer,
        ForeignKey("incidentes.id", ondelete="CASCADE"),
        nullable=False
    )
    mecanico_id = Column(Integer, ForeignKey("mecanicos.id", ondelete="SET NULL"), nullable=True)


    # --- Relaciones ---
    incidente = relationship("Incidente", back_populates="asignacion")
    mecanico  = relationship("Mecanico",  back_populates="asignaciones")