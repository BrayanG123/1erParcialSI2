from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.core.dependencies import get_current_superadmin
from app.models.usuario import Usuario, RolUsuario, Administrador
from app.models.taller import Taller
from app.schemas.taller import TallerCreate
from app.crud.taller import get_all_talleres, crear_taller
from app.services.bitacora import BitacoraService
from app.schemas.bitacora import BitacoraRead


router = APIRouter(
    prefix="/superadmin",
    tags=["Superadmin"],
    dependencies=[Depends(get_current_superadmin)],
)


@router.get("/bitacora", response_model=list[BitacoraRead])
def ver_bitacora(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Bitácora global de auditoría (Solo Superadmin).
    """
    return BitacoraService.obtener_todos(db, skip=skip, limit=limit)


@router.get("/kpis")
def kpis(db: Session = Depends(get_db)):
    """
    KPIs globales para el dashboard del superadmin.
    """
    total_usuarios = db.query(func.count(Usuario.id)).scalar() or 0
    total_talleres = db.query(func.count(Taller.id)).scalar() or 0
    total_admins = db.query(func.count(Usuario.id)).filter(Usuario.rol == RolUsuario.administrador).scalar() or 0
    total_clientes = db.query(func.count(Usuario.id)).filter(Usuario.rol == RolUsuario.cliente).scalar() or 0

    return {
        "total_usuarios": total_usuarios,
        "total_talleres": total_talleres,
        "total_admins": total_admins,
        "total_clientes": total_clientes,
    }


@router.get("/talleres")
def listar_talleres(db: Session = Depends(get_db)):
    """
    Tabla global de talleres (para gestión).
    """
    talleres = get_all_talleres(db)

    # Se devuelve un shape simple para el frontend
    data = []
    for t in talleres:
        admin_id = None
        admin_usuario_id = None
        if t.administrador:
            admin_id = t.administrador.id
            admin_usuario_id = t.administrador.usuario_id

        data.append(
            {
                "id": t.id,
                "nombre": t.nombre,
                "direccion": t.direccion,
                "telefono": t.telefono,
                "latitud": t.latitud,
                "longitud": t.longitud,
                "calificacion_promedio": t.calificacion_promedio,
                "is_active": t.is_active,
                "administrador_id": admin_id,
                "administrador_usuario_id": admin_usuario_id,
            }
        )
    return data


@router.patch("/talleres/{taller_id}")
def editar_taller(taller_id: int, datos: dict, db: Session = Depends(get_db)):
    """
    Edita un taller (Solo Superadmin).
    Permite baja lógica cambiando is_active.
    """
    taller = db.query(Taller).filter(Taller.id == taller_id).first()
    if not taller:
        return {"error": "Taller no encontrado"}, 404
    
    for key, value in datos.items():
        if hasattr(taller, key):
            setattr(taller, key, value)
    
    db.commit()
    db.refresh(taller)
    return taller


@router.post("/talleres")
def registrar_taller(datos: TallerCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo taller en el sistema (Solo Superadmin).
    """
    return crear_taller(db, admin_id=None, datos=datos)


@router.get("/usuarios")
def listar_usuarios(db: Session = Depends(get_db)):
    """
    Lista global de usuarios (supervisión).
    """
    usuarios = db.query(Usuario).order_by(Usuario.id.desc()).all()
    return [
        {
            "id": u.id,
            "nombre": u.nombre,
            "apellido": u.apellido,
            "email": u.email,
            "username": u.username,
            "rol": u.rol.value if hasattr(u.rol, "value") else str(u.rol),
            "is_active": u.is_active,
            "fecha_creacion": u.fecha_creacion,
        }
        for u in usuarios
    ]


@router.put("/usuarios/{usuario_id}")
def editar_usuario(usuario_id: int, datos: dict, db: Session = Depends(get_db)):
    """
    Edita cualquier usuario (Solo Superadmin).
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return {"error": "Usuario no encontrado"}, 404
    
    for key, value in datos.items():
        if hasattr(usuario, key):
            setattr(usuario, key, value)
    
    db.commit()
    db.refresh(usuario)
    return usuario


@router.patch("/usuarios/{usuario_id}/suspender")
def suspender_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """
    Alterna el estado de activación de un usuario.
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return {"error": "Usuario no encontrado"}, 404
    
    usuario.is_active = not usuario.is_active
    db.commit()
    return {"message": "Estado actualizado", "is_active": usuario.is_active}


@router.delete("/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """
    Elimina un usuario del sistema.
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return {"error": "Usuario no encontrado"}, 404
    
    db.delete(usuario)
    db.commit()
    return {"message": "Usuario eliminado"}

