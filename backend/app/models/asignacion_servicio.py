import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base


class EstadoAsignacion(str, enum.Enum):
    pendiente   = "pendiente"
    buscando_taller  = "buscando_taller"
    taller_asignado  = "taller_asignado"
    en_camino        = "en_camino"
    en_atencion      = "en_atencion"
    finalizado       = "finalizado"
    cancelado        = "cancelado"
    rechazada        = "rechazada"


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

    # ---  FK hacia tenants ---
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )


    # --- Relaciones ---
    incidente = relationship("Incidente", back_populates="asignacion")
    mecanico  = relationship("Mecanico",  back_populates="asignaciones")
    tenant    = relationship("Tenant",    back_populates="asignaciones")
    servicio_realizado = relationship(
        "ServicioRealizado",
        back_populates="asignacion",
        uselist=False   # 1:1 — devuelve un objeto, no una lista
    )
    historial = relationship(
        "HistorialEstado",
        back_populates="asignacion",
        order_by="HistorialEstado.fecha_cambio"
    )