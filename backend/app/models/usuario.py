from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base



class RolUsuario(str, enum.Enum):
    superadmin = "superadmin" 
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

    # ── NUEVO: token FCM del dispositivo del usuario ─────────────────────────
    # Cada vez que el usuario inicia sesión en un dispositivo, la app enviara este token al backend. Se sobreescribe si el usuario cambia de dispositivo.
    push_token = Column(String(500), nullable=True)

    # Relaciones con las tablas de perfil (una a una)
    perfil_cliente = relationship("Cliente", back_populates="usuario", uselist=False)
    perfil_mecanico = relationship("Mecanico", back_populates="usuario", uselist=False)
    perfil_administrador = relationship("Administrador", back_populates="usuario", uselist=False)

    notificaciones = relationship("Notificacion", back_populates="usuario")


# TABLA PERFIL: clientes
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer, 
        ForeignKey("usuarios.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )
    foto_perfil = Column(String(500), nullable=True)

    # relacion inversa hacia Usuario
    usuario = relationship("Usuario", back_populates="perfil_cliente")
    vehiculos = relationship("Vehiculo", back_populates="cliente")
    incidentes = relationship("Incidente", back_populates="cliente")


# tabla perfil: mecanicos
class Mecanico(Base):
    __tablename__ = "mecanicos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False)
    taller_id = Column(Integer, ForeignKey("talleres.id", ondelete="SET NULL"), nullable=True) 
    # Especialidades del mecánico: se guardan VARIAS en esta misma columna,
    # separadas por comas (ej: "Motor y transmisión, Sistema eléctrico").
    # La API siempre las expone como lista vía la property de abajo.
    especialidad = Column(String(200), nullable=True)
    estado = Column(String(50), default="disponible", nullable=False)
    telefono = Column(String(20), nullable=True)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    foto_vehiculo = Column(String(500), nullable=True)
    tipo_seguro = Column(String(100), nullable=True)

    # FK hacia tenants ---
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relacion inversa hacia Usuario
    usuario = relationship("Usuario", back_populates="perfil_mecanico")
    taller = relationship("Taller", back_populates="mecanicos")
    tenant = relationship("Tenant",  back_populates="mecanicos")
    asignaciones = relationship("AsignacionServicio", back_populates="mecanico")

    @property
    def especialidades(self) -> list[str]:
        """La columna 'especialidad' (texto separado por comas) como lista limpia."""
        if not self.especialidad:
            return []
        return [e.strip() for e in self.especialidad.split(",") if e.strip()]


class Administrador(Base):
    __tablename__ = "administradores"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False)
    taller_id = Column(Integer, ForeignKey("talleres.id", ondelete="SET NULL"), nullable=True)

    # FK hacia tenants ---
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    usuario = relationship("Usuario", back_populates="perfil_administrador")

    # ← Agrega foreign_keys para resolver la ambigüedad
    taller = relationship(
        "Taller", 
        back_populates="administrador", 
        uselist=False, 
        foreign_keys=[taller_id]
    )
    tenant  = relationship("Tenant", back_populates="administradores")