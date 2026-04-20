from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioRead
from app.crud.usuario import get_usuarios, get_usuario_by_id, desactivar_usuario
from app.core.dependencies import get_current_administrador
from app.services.bitacora import BitacoraService
from app.schemas.bitacora import BitacoraRead


router = APIRouter(
    prefix="/admin",
    tags=["Administracion"],
    dependencies=[Depends(get_current_administrador)]
)

@router.get("/bitacora", response_model=list[BitacoraRead])
def ver_bitacora(skip: int=0, limit: int=50, db: Session=Depends(get_db),):
    """Retorna los últimos eventos de la bitácora (solo administradores)."""
    return BitacoraService.obtener_todos(db, skip=skip, limit=limit)

@router.get("/bitacora/usuario/{usuario_id}", response_model=list[BitacoraRead])
def ver_bitacora_usuario(
    usuario_id: int,
    skip: int=0,
    limit: int=50,
    db: Session=Depends(get_db)
):
    """Retorna los eventos de un usuario específico (solo administradores)."""
    return BitacoraService.obtener_por_usuario(db, usuario_id=usuario_id, skip=skip, limit=limit)



@router.get("/usuarios", response_model=list[UsuarioRead])
def listar_todos_los_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista todos los usuarios del sistema."""
    return get_usuarios(db, skip=skip, limit=limit)


@router.get("/usuarios/{usuario_id}", response_model=UsuarioRead)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Obtiene un usuario por ID."""
    usuario = get_usuario_by_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_usuario_admin(usuario_id: int, db: Session = Depends(get_db)):
    """Desactiva un usuario. Solo administradores."""
    usuario = get_usuario_by_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    desactivar_usuario(db, usuario)