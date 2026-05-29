from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.core.dependencies import get_current_superadmin
from app.models.usuario import Usuario, RolUsuario, Administrador, Mecanico
from app.models.taller import Taller
from app.models.tenant import Tenant
from app.models.asignacion_servicio import AsignacionServicio
from app.schemas.taller import TallerCreate
from app.schemas.tenant import TenantCreate, TenantRead, TenantUpdate, TenantConEstadisticas
from app.crud.taller import get_all_talleres, crear_taller
from app.services.bitacora import BitacoraService
from app.schemas.bitacora import BitacoraRead


router = APIRouter(
    prefix="/superadmin",
    tags=["Superadmin"],
    dependencies=[Depends(get_current_superadmin)],
)


# ============================================================
# BITÁCORA
# ============================================================
@router.get("/bitacora", response_model=list[BitacoraRead])
def ver_bitacora(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Bitácora global de auditoría (Solo Superadmin).
    """
    return BitacoraService.obtener_todos(db, skip=skip, limit=limit)


# ============================================================
# KPIs GLOBALES
# ============================================================
@router.get("/kpis")
def kpis(db: Session = Depends(get_db)):
    """
    KPIs globales para el dashboard del superadmin.
    """
    total_usuarios = db.query(func.count(Usuario.id)).scalar() or 0
    total_talleres = db.query(func.count(Taller.id)).scalar() or 0
    total_admins = db.query(func.count(Usuario.id)).filter(Usuario.rol == RolUsuario.administrador).scalar() or 0
    total_clientes = db.query(func.count(Usuario.id)).filter(Usuario.rol == RolUsuario.cliente).scalar() or 0
    total_tenants  = db.query(func.count(Tenant.id)).scalar() or 0

    return {
        "total_usuarios": total_usuarios,
        "total_talleres": total_talleres,
        "total_admins": total_admins,
        "total_clientes": total_clientes,
        "total_tenants":   total_tenants,
    }


# ============================================================
# TALLERES (gestión global)
# ============================================================
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
                "tenant_id": t.tenant_id,
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
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    
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


# ============================================================
# USUARIOS (supervisión)
# ============================================================
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
            # "rol": u.rol.value if hasattr(u.rol, "value") else str(u.rol),
            "rol":      u.rol.value,
            "is_active": u.is_active,
            "fecha_creacion": u.fecha_creacion,
        }
        for u in usuarios
    ]



# ============================================================
# TENANTS — CRUD completo (Solo Superadmin)
# ============================================================

@router.get("/tenants", response_model=list[TenantRead])
def listar_tenants(db: Session = Depends(get_db)):
    """Lista todos los tenants del sistema."""
    return db.query(Tenant).order_by(Tenant.id).all()

@router.get("/tenants/{tenant_id}", response_model=TenantConEstadisticas)
def ver_tenant(tenant_id: int, db: Session = Depends(get_db)):
    """Detalle de un tenant con estadísticas de sus recursos."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    total_talleres = db.query(func.count(Taller.id)).filter(
        Taller.tenant_id == tenant_id
    ).scalar() or 0

    total_mecanicos = db.query(func.count(Mecanico.id)).filter(
        Mecanico.tenant_id == tenant_id
    ).scalar() or 0

    total_admins = db.query(func.count(Administrador.id)).filter(
        Administrador.tenant_id == tenant_id
    ).scalar() or 0

    total_asignaciones = db.query(func.count(AsignacionServicio.id)).filter(
        AsignacionServicio.tenant_id == tenant_id
    ).scalar() or 0

    return TenantConEstadisticas(
        id=tenant.id,
        nombre=tenant.nombre,
        plan=tenant.plan,
        activo=tenant.activo,
        fecha_registro=tenant.fecha_registro,
        total_talleres=total_talleres,
        total_mecanicos=total_mecanicos,
        total_admins=total_admins,
        total_asignaciones=total_asignaciones,
    )

@router.post("/tenants", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
def crear_tenant(
    datos: TenantCreate,
    db: Session = Depends(get_db),
    superadmin: Usuario = Depends(get_current_superadmin),
):
    """Crea un nuevo tenant en el sistema."""
    existente = db.query(Tenant).filter(Tenant.nombre == datos.nombre).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un tenant con ese nombre")

    nuevo = Tenant(
        nombre=datos.nombre,
        plan=datos.plan,
        activo=datos.activo,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    BitacoraService.registrar(
        db=db,
        accion="CREAR_TENANT",
        descripcion=f"Tenant creado: {nuevo.nombre} (plan: {nuevo.plan.value})",
        usuario_id=superadmin.id,
        entidad_afectada="tenants",
    )

    return nuevo

@router.patch("/tenants/{tenant_id}", response_model=TenantRead)
def actualizar_tenant(
    tenant_id: int,
    datos: TenantUpdate,
    db: Session = Depends(get_db),
    superadmin: Usuario = Depends(get_current_superadmin),
):
    """Actualiza nombre, plan o estado activo de un tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    if datos.nombre is not None:
        tenant.nombre = datos.nombre
    if datos.plan is not None:
        tenant.plan = datos.plan
    if datos.activo is not None:
        tenant.activo = datos.activo

    db.commit()
    db.refresh(tenant)

    BitacoraService.registrar(
        db=db,
        accion="ACTUALIZAR_TENANT",
        descripcion=f"Tenant actualizado: {tenant.nombre}",
        usuario_id=superadmin.id,
        entidad_afectada="tenants",
    )

    return tenant


@router.post("/tenants/{tenant_id}/asignar-taller/{taller_id}")
def asignar_taller_a_tenant(
    tenant_id: int,
    taller_id: int,
    db: Session = Depends(get_db),
    superadmin: Usuario = Depends(get_current_superadmin),
):
    """
    Asigna un taller a un tenant.
    También actualiza el tenant_id del administrador y mecánicos del taller.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    taller = db.query(Taller).filter(Taller.id == taller_id).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    # Asignar el taller al tenant
    taller.tenant_id = tenant_id

    # Asignar al administrador del taller
    if taller.administrador:
        taller.administrador.tenant_id = tenant_id

    # Asignar a todos los mecánicos del taller
    for mecanico in taller.mecanicos:
        mecanico.tenant_id = tenant_id

    db.commit()

    return {
        "mensaje": f"Taller '{taller.nombre}' asignado al tenant '{tenant.nombre}'",
        "mecanicos_actualizados": len(taller.mecanicos),
    }


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

