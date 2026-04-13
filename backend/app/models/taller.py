from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class Taller(Base):
    __tablename__ = "talleres"

    id = Column(Integer, primary_key=True, index=True)
    administrador_id = Column(Integer, ForeignKey("administradores.id", ondelete="SET NULL"), nullable=True)
    nombre = Column(String(200), nullable=False)
    direccion = Column(String(500), nullable=False)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    telefono = Column(String(20), nullable=True)
    calificacion_promedio = Column(Float, default=0.0, nullable=True)

    # realcion de uno a uno taller----administrador
    administrador = relationship("Administrador", back_populates="taller")

    # relacion uno a muchos taller-----mecanico
    mecanicos = relationship("Mecanico", back_populates="taller")