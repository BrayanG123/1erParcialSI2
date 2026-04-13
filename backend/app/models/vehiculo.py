from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class Vehiculo(Base):
    __tablename__ = "vehiculos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    placa = Column(String(20), unique=True, nullable=False, index=True)
    modelo = Column(String(100), nullable=False)
    color = Column(String(100), nullable=False)
    foto_vehiculo = Column(String(500), nullable=True)
    tipo_seguro = Column(String(100), nullable=True)

    cliente = relationship("Cliente", back_populates="vehiculos")

    