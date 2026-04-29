from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario, Mecanico
from app.schemas.usuario import UsuarioRead, UsuarioCreate
from app.crud.usuario import desactivar_usuario, crear_usuario
from app.core.dependencies import get_current_administrador
from app.services.bitacora import BitacoraService
from app.schemas.bitacora import BitacoraRead

router = APIRouter(
    prefix="/admin",
    tags=["Administracion"],
    dependencies=[Depends(get_current_administrador)]
)

@router.get("/bitacora", response_model=list[BitacoraRead])
def ver_bitacora(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_administrador),
):
    # Cada admin solo ve eventos de su propio usuario y mecánicos de su taller
    taller_id = usuario.perfil_administrador.taller_id

    mecanicos_ids = [
        m.usuario_id for m in
        db.query(Mecanico).filter(Mecanico.taller_id == taller_id).all()
    ]
    usuarios_del_taller = [usuario.id] + mecanicos_ids

    return BitacoraService.obtener_por_usuarios(
        db, usuario_ids=usuarios_del_taller, skip=skip, limit=limit
    )

@router.get("/usuarios", response_model=list[UsuarioRead])
def listar_mecanicos_del_taller(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_administrador),
):
    # Solo mecánicos de su taller
    taller_id = usuario.perfil_administrador.taller_id
    mecanicos = (
        db.query(Mecanico)
        .filter(Mecanico.taller_id == taller_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [m.usuario for m in mecanicos]

@router.get("/usuarios/{usuario_id}", response_model=UsuarioRead)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_administrador),
):
    taller_id = usuario.perfil_administrador.taller_id

    # Verificar que el usuario es mecánico de su taller
    mecanico = (
        db.query(Mecanico)
        .filter(
            Mecanico.usuario_id == usuario_id,
            Mecanico.taller_id == taller_id
        )
        .first()
    )
    if not mecanico:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en tu taller")
    return mecanico.usuario

@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_usuario_admin(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_administrador),
):
    taller_id = usuario.perfil_administrador.taller_id

    mecanico = (
        db.query(Mecanico)
        .filter(
            Mecanico.usuario_id == usuario_id,
            Mecanico.taller_id == taller_id
        )
        .first()
    )
    if not mecanico:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en tu taller")
    desactivar_usuario(db, mecanico.usuario)

@router.post("/usuarios", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def registrar_mecanico(
    datos: UsuarioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_administrador),
):
    """
    Registra un nuevo mecánico y lo asigna automáticamente al taller del admin.
    """
    taller_id = usuario.perfil_administrador.taller_id
    if not taller_id:
        raise HTTPException(status_code=400, detail="No tienes un taller configurado")
    
    return crear_usuario(db, datos, taller_id=taller_id)