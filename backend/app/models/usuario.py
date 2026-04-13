from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base



class RolUsuario(str, enum.Enum):
    cliente = "cliente"
    mecanico = "mecanico"
    administrador = "administrador"


# tabla base: usuarios
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(SAEnum(RolUsuario), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones con las tablas de perfil (una a una)
    perfil_cliente = relationship("Cliente", back_populates="usuario", uselist=False)
    perfil_mecanico = relationship("Mecanico", back_populates="usuario", uselist=False)
    perfil_administrador = relationship("Administrador", back_populates="usuario", uselist=False)



# TABLA PERFIL: clientes
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, 
                       ForeignKey("usuarios.id", ondelete="CASCADE"), 
                       unique=True, 
                       nullable=False
                       )
    foto_perfil = Column(String(500), nullable=True)

    # relacion inversa hacia Usuario
    usuario = relationship("Usuario", back_populates="perfil_cliente")


# tabla perfil: mecanicos
class Mecanico(Base):
    __tablename__ = "mecanicos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False)
    especialidad = Column(String(200), nullable=True)
    estado = Column(String(50), default="disponible", nullable=False)
    telefono = Column(String(20), nullable=True)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    foto_vehiculo = Column(String(500), nullable=True)
    tipo_seguro = Column(String(100), nullable=True)

    # Relacion inversa hacia Usuario
    usuario = relationship("Usuario", back_populates="perfil_mecanico")


# Tabla de perfil: administradores
class Administrador(Base):
    __tablename__ = "administradores"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Relacion inversa hacia usuario
    usuario = relationship("Usuario", back_populates="perfil_administrador")