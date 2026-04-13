from typing import Optional
from sqlalchemy.orm import Session

from app.models.usuario import Usuario, Cliente, Mecanico, Administrador, RolUsuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.core.security import hash_password


# LECTURAS (Read)
def get_usuario_by_id(db: Session, usuario_id: int) -> Optional[Usuario]:
    """Busca un usuario por su ID."""
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def get_usuario_by_email(db: Session, email: str) -> Optional[Usuario]:
    """Busca un usuario por email. Usado en login y validación de duplicados."""
    return db.query(Usuario).filter(Usuario.email == email).first()

def get_usuario_by_username(db: Session, username: str) -> Optional[Usuario]:
    """Busca un usuario por username."""
    return db.query(Usuario).filter(Usuario.username == username).first()


def get_usuarios(db: Session, skip: int = 0, limit: int = 100) -> list[Usuario]:
    """Retorna una lista paginada de usuarios."""
    return db.query(Usuario).offset(skip).limit(limit).all()


# CREATE
def crear_usuario(db: Session, datos: UsuarioCreate) -> Usuario:
    """
    Crea un nuevo usuario con su perfil correspondiente según el rol.
    Todo en una sola transacción.
    """
    # 1. Crear el usuario base
    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        apellido=datos.apellido,
        email=datos.email,
        username=datos.username,
        password_hash=hash_password(datos.password),
        rol=datos.rol
    )

    db.add(nuevo_usuario)
    db.flush() # obtiene el ID generado sin hacer commit todavía

    # 2. Crear el perfil según el rol
    if datos.rol == RolUsuario.cliente:
        perfil = Cliente(usuario_id=nuevo_usuario.id)
        db.add(perfil)

    elif datos.rol == RolUsuario.mecanico:
        perfil = Mecanico(usuario_id=nuevo_usuario.id)
        db.add(perfil)

    elif datos.rol == RolUsuario.administrador:
        perfil = Administrador(usuario_id=nuevo_usuario.id)
        db.add(perfil)

    # 3. Confirmar toda la operación de una vez
    db.commit()
    db.refresh(nuevo_usuario) # recarga el objeto con los datos de la DB (id, fecha_creacion, etc.)

    return nuevo_usuario


# ACTUALIZACIÓN (Update)
def actualizar_usuario(db: Session, usuario: Usuario, datos: UsuarioUpdate) -> Usuario:
    """
    Actualiza solo los campos que vienen con valor (no None).
    """
    datos_dict = datos.model_dump(exclude_unset=True) # solo los campos enviados

    for campo, valor in datos_dict.items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return usuario


# ELIMINACIÓN (Delete)
def desactivar_usuario(db: Session, usuario: Usuario) -> Usuario:
    """
    Soft delete: marca el usuario como inactivo en lugar de borrarlo.
    Esto preserva la integridad referencial con otras tablas.
    """
    usuario.is_active = False
    db.commit()
    db.refresh(usuario)
    return usuario