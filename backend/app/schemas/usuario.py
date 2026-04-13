from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re

from app.models.usuario import RolUsuario


# Base: campos cimunes a varios schemas
class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    username: str


# create - datos que llegan al registrarse
class UsuarioCreate(UsuarioBase):
    password: str
    rol: RolUsuario

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if len(v) < 5:
            raise ValueError("La contraseña debe tener al menos 5 caracteres")
        return v
    
    @field_validator("username")
    @classmethod
    def validar_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,50}$", v):
            raise ValueError("El username solo puede tener letras, números y guiones bajos (3-50 caracteres)")
        return v


# READ - lo que retorna la API (sin password)
class UsuarioRead(UsuarioBase):
    id: int
    rol: RolUsuario
    is_active: bool
    fecha_creacion: datetime

    model_config = {"from_attributes": True}


# UPDATE - campos que se pueden modificar (todos opcionales)
class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    username: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validar_username(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^[a-zA-Z0-9_]{3,50}$", v):
            raise ValueError("El username solo puede tener letras, números y guiones bajos (3-50 caracteres)")
        return v
    


# SCHEMAS DEL PERFIL
class ClienteCreate(BaseModel):
    foto_perfil: Optional[str] = None


class ClienteRead(BaseModel):
    id: int
    usuario_id: int
    foto_perfil: Optional[str]

    model_config = {"from_attributes": True}


class MecanicoCreate(BaseModel):
    especialidad: Optional[str] = None
    telefono: Optional[str] = None


class MecanicoRead(BaseModel):
    id: int
    usuario_id: int
    especialidad: Optional[str]
    estado: str
    telefono: Optional[str]
    latitud: Optional[float]
    longitud: Optional[float]

    model_config = {"from_attributes": True}


# SCHEMA COMPUESTO - usuario con su perfil incluido
class UsuarioConPerfil(UsuarioRead):
    perfil_cliente: Optional[ClienteRead] = None
    perfil_mecanico: Optional[MecanicoRead] = None



# ============================================================
# SCHEMAS DE AUTENTICACIÓN
# ============================================================
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Datos extraídos del payload del JWT."""
    usuario_id: Optional[int] = None
    rol: Optional[int] = None
    type: Optional[int] = None

    