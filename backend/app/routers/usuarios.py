from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.usuario import Usuario, Administrador, Mecanico, Cliente
from app.schemas.usuario import (
    UsuarioRead, UsuarioUpdate, UsuarioConPerfil,
    EspecialidadesUpdate, MecanicoRead,
)
from app.crud.usuario import get_usuario_by_id, actualizar_usuario, desactivar_usuario
from app.core.dependencies import get_current_usuario, get_current_administrador



router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)


# Catálogo canónico de especialidades del sistema.
# Coherente con el seeder y con ESPECIALIDADES_POR_CATEGORIA del
# asignador inteligente (services/ia/asignador_inteligente.py).
ESPECIALIDADES_CATALOGO = [
    "Motor y transmisión",
    "Sistema eléctrico",
    "Frenos y dirección",
    "Llantas y suspensión",
    "Chapería y pintura",
    "Aire acondicionado",
    "Diagnóstico general",
    "Auxilio en ruta",
]


# ── Especialidades de mecánicos (múltiples por mecánico) ─────────────────────

@router.get("/especialidades/catalogo")
def catalogo_especialidades(
    usuario: Usuario = Depends(get_current_usuario),
):
    """Lista de especialidades disponibles (para selects/checkboxes en el front)."""
    return {"especialidades": ESPECIALIDADES_CATALOGO}


@router.put("/me/especialidades", response_model=MecanicoRead)
def actualizar_mis_especialidades(
    datos: EspecialidadesUpdate,
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    """El MECÁNICO autenticado actualiza sus propias especialidades."""
    if not usuario.perfil_mecanico:
        raise HTTPException(status_code=403, detail="Solo los mecánicos tienen especialidades")

    perfil = usuario.perfil_mecanico
    perfil.especialidad = ", ".join(datos.especialidades) or None
    db.commit()
    db.refresh(perfil)
    return perfil


@router.put("/mecanicos/{mecanico_id}/especialidades", response_model=MecanicoRead)
def actualizar_especialidades_mecanico(
    mecanico_id: int,
    datos: EspecialidadesUpdate,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """El ADMIN actualiza las especialidades de un mecánico de SU taller."""
    mecanico = db.query(Mecanico).filter(Mecanico.id == mecanico_id).first()
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")

    if mecanico.taller_id != usuario.perfil_administrador.taller_id:
        raise HTTPException(status_code=403, detail="Este mecánico no pertenece a tu taller")

    mecanico.especialidad = ", ".join(datos.especialidades) or None
    db.commit()
    db.refresh(mecanico)
    return mecanico


@router.get("/me", response_model=UsuarioConPerfil)
def mi_perfil(
    usuario_actual: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db)
):
    """Retorna el perfil completo del usuario autenticado, incluyendo taller si es admin."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_actual.id).options(
        joinedload(Usuario.perfil_administrador).joinedload(Administrador.taller),
        joinedload(Usuario.perfil_mecanico).joinedload(Mecanico.taller),
        joinedload(Usuario.perfil_cliente)
    ).first()
    
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