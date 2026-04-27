import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base


class EstadoIncidente(str, enum.Enum):
    disponible = "disponible"
    no_disponible = "no_disponible"


class Incidente(Base):
    __tablename__ = "incidentes"

    id          = Column(Integer, primary_key=True, index=True)
    descripcion = Column(Text, nullable=False)
    fecha_hora  = Column(DateTime, default=datetime.utcnow, nullable=False)
    latitud     = Column(Float, nullable=False)
    longitud    = Column(Float, nullable=False)
    estado      = Column(SAEnum(EstadoIncidente), default=EstadoIncidente.disponible, nullable=False)
    resumen_ia  = Column(Text, nullable=True)   # resumenIA del diagrama
    foto_incidente = Column(String(500), nullable=True)

    # --- Foreign Keys ---
    cliente_id  = Column(Integer, ForeignKey("clientes.id",  ondelete="CASCADE"),  nullable=False)
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id", ondelete="SET NULL"), nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True)

    # --- Relaciones ---
    cliente  = relationship("Cliente",  back_populates="incidentes")
    vehiculo = relationship("Vehiculo", back_populates="incidentes")
    categoria = relationship("Categoria", back_populates="incidentes")
    asignacion = relationship("AsignacionServicio", back_populates="incidente", uselist=False)
    evidencias = relationship("Evidencia", back_populates="incidente")
    # procesamientos_ia = relationship("ProcesamientoIA", back_populates="incidente")
