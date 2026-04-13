from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioRead, UsuarioUpdate, UsuarioConPerfil
from app.crud.usuario import get_usuario_by_id, actualizar_usuario, desactivar_usuario
from app.core.dependencies import get_current_usuario, get_current_administrador



router = APIRouter(
    prefix="/usuarios", 
    tags=["Usuarios"]
)


@router.get("/me", response_model=UsuarioConPerfil)
def mi_perfil(usuario: Usuario = Depends(get_current_usuario)):
    """Retorna el perfil del usuario autenticado."""
    return usuario

@router.patch("/me", response_model=UsuarioRead)
def actualizar_mi_perfil(
    datos: UsuarioUpdate,
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db)
):
    """Actualiza los datos del usuario autenticado."""
    return actualizar_usuario(db, usuario, datos)

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_mi_cuenta(
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db)
):
    """Desactiva la cuenta del usuario autenticado."""
    desactivar_usuario(db, usuario)


# --- Endpoints de administrador ---
# @router.get("/", response_model=list[UsuarioRead])
# def listar_usuarios(
#     skip: int=0,
#     limit: int=100,
#     admin: Usuario = Depends(get_current_admin),
#     db: Session = Depends(get_db)
# ):
#     """Lista todos los usuarios. Solo administradores."""
#     from app.crud.usuario import get_usuarios
#     return get_usuarios(db, skip=skip, limit=limit)


# @router.get("/{usuario_id}", response_model=UsuarioConPerfil)
# def obtener_usuario(
#     usuario_id: int,
#     admin: Usuario = Depends(get_current_admin), # solo admins
#     db: Session = Depends(get_db)
# ):
    
#     usuario = get_usuario_by_id(db, usuario_id)
#     if not usuario:
#         raise HTTPException(status_code=404, detail="Usuario no encontrado")
#     return usuario