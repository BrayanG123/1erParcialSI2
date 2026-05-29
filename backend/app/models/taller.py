from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base


class Taller(Base):
    __tablename__ = "talleres"

    id = Column(Integer, primary_key=True, index=True)

    nombre = Column(String(200), nullable=False)
    direccion = Column(String(500), nullable=False)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    telefono = Column(String(20), nullable=True)
    calificacion_promedio = Column(Float, default=0.0, nullable=True)
    is_active = Column(Boolean, default=True)

    # FK hacia tenants ---
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,     # índice para filtrar rápido por tenant
    )

    # --- Relaciones ---
    tenant = relationship("Tenant", back_populates="talleres")
    # relacion de uno a uno taller----administrador
    administrador = relationship("Administrador", back_populates="taller", foreign_keys="Administrador.taller_id", uselist=False)

    # relacion uno a muchos taller-----mecanico
    mecanicos = relationship("Mecanico", back_populates="taller")