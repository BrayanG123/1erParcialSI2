from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.usuario import Usuario, Administrador
from app.schemas.taller import TallerCreate, TallerRead
from app.crud.taller import get_all_talleres, get_taller_by_admin, crear_taller
from app.core.dependencies import get_current_administrador, get_current_superadmin

router = APIRouter(prefix="/talleres", tags=["Talleres"])

@router.get("/", response_model=List[TallerRead])
def listar_talleres_publico(db: Session = Depends(get_db)):
    """Lista todos los talleres (público o compartido)."""
    return get_all_talleres(db)

@router.get("/mi-taller")
def obtener_mi_taller(
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_administrador)
):
    """Retorna el taller asociado al administrador autenticado."""
    perfil_admin = db.query(Administrador).filter(Administrador.usuario_id == admin.id).first()
    if not perfil_admin:
        raise HTTPException(status_code=404, detail="Perfil de administrador no encontrado")
    
    taller = get_taller_by_admin(db, perfil_admin.id)
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no configurado")
    return taller
