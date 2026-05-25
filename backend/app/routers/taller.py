from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.usuario import Usuario, Administrador
from app.schemas.taller import TallerCreate, TallerUpdate, TallerRead
from app.crud.taller import ( crear_taller, get_taller_por_id, get_taller_de_admin, get_talleres, actualizar_taller, eliminar_taller, get_all_talleres, get_taller_by_admin,)
from app.core.dependencies import get_current_administrador
from app.services.bitacora import BitacoraService

router = APIRouter(prefix="/talleres", tags=["Talleres"])


# ── PÚBLICO — listar todos los talleres ──────────────────────────────────────
@router.get("/", response_model=list[TallerRead])
def listar_talleres_publico( db: Session = Depends(get_db)):
    """Lista todos los talleres (público o compartido)."""
    return get_talleres(db)


# ── PÚBLICO — ver un taller por ID ───────────────────────────────────────────
@router.get("/{taller_id}", response_model=TallerRead)
def obtener_taller(taller_id: int, db: Session = Depends(get_db)):
    taller = get_taller_por_id(db, taller_id)
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return taller


# ── ADMIN — ver su propio taller ─────────────────────────────────────────────
@router.get("/mi-taller", response_model=TallerRead)
def mi_taller(
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_administrador)
):
    """Retorna el taller asociado al administrador autenticado."""
    # admin = usuario.perfil_administrador
    # taller = get_taller_de_admin(db, admin.id)
    perfil_admin = db.query(Administrador).filter(Administrador.usuario_id == admin.id).first()
    if not perfil_admin:
        raise HTTPException(status_code=404, detail="Perfil de administrador no encontrado")
    
    taller = get_taller_by_admin(db, perfil_admin.id)
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no configurado")
    return taller


# ── ADMIN — crear taller ─────────────────────────────────────────────────────
@router.post("/", response_model=TallerRead, status_code=status.HTTP_201_CREATED)
def crear_mi_taller(
    datos: TallerCreate,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    admin = usuario.perfil_administrador

    existente = get_taller_de_admin(db, admin.id)
    if existente:
        raise HTTPException(status_code=400, detail="Ya tienes un taller registrado")

    taller = crear_taller(db, admin.id, datos)

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="CREAR_TALLER",
        descripcion=f"Taller '{taller.nombre}' creado con id #{taller.id}",
    )
    return taller


# ── ADMIN — actualizar su taller ─────────────────────────────────────────────
@router.patch("/{taller_id}", response_model=TallerRead)
def actualizar_mi_taller(
    taller_id: int,
    datos: TallerUpdate,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller = get_taller_por_id(db, taller_id)
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    admin = usuario.perfil_administrador
    if admin.taller_id != taller.id:
        raise HTTPException(status_code=403, detail="Este taller no es tuyo")

    taller = actualizar_taller(db, taller, datos)

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="ACTUALIZAR_TALLER",
        descripcion=f"Taller #{taller_id} actualizado",
    )
    return taller


# ── ADMIN — eliminar taller ──────────────────────────────────────────────────
@router.delete("/{taller_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_mi_taller(
    taller_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller = get_taller_por_id(db, taller_id)
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    admin = usuario.perfil_administrador
    if admin.taller_id != taller.id:
        raise HTTPException(status_code=403, detail="Este taller no es tuyo")

    eliminar_taller(db, taller)

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="ELIMINAR_TALLER",
        descripcion=f"Taller #{taller_id} eliminado",
    )
