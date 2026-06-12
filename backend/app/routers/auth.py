from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import RolUsuario, Administrador, Usuario
from app.schemas.usuario import Token, UsuarioCreate, UsuarioRead
from app.schemas.taller import TallerCreate
from app.crud.usuario import (
    get_usuario_by_email,
    get_usuario_by_username,
    crear_usuario,
    get_usuario_by_id,
)
from app.crud.taller import get_taller_by_admin, crear_taller
from app.core.security import verify_password, crear_access_token, crear_refresh_token
from app.services.bitacora import BitacoraService
from app.core.dependencies import get_current_usuario, require_roles

router = APIRouter(
    prefix="/auth", 
    tags=["Autenticacion"]
)

# ============================================================
# REGISTRO SIMPLE (PASO 1)
# ============================================================
@router.post("/registro", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def registro(datos: UsuarioCreate, db: Session = Depends(get_db)):
    if get_usuario_by_email(db, datos.email):
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    if get_usuario_by_username(db, datos.username):
        raise HTTPException(status_code=400, detail="El username ya está en uso")
    
    nuevo = crear_usuario(db, datos)
    BitacoraService.registrar(
        db=db,
        accion="REGISTRO",
        descripcion=f"Nuevo usuario: {nuevo.username} ({nuevo.rol})",
        usuario_id=nuevo.id
    )
    return nuevo

# ============================================================
# LOGIN (CORREGIDO)
# ============================================================
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 1. Buscar el usuario (por email o por username)
    usuario = get_usuario_by_email(db, form_data.username)
    if not usuario:
        usuario = get_usuario_by_username(db, form_data.username)

    # 2. Validar credenciales
    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        BitacoraService.registrar(
            db=db,
            accion="LOGIN_FALLIDO",
            descripcion=f"Intento fallido: {form_data.username}",
            usuario_id=usuario.id if usuario else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not usuario.is_active:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    rol_valor = usuario.rol.value if hasattr(usuario.rol, "value") else str(usuario.rol)

    # 3. Determinar el tenant_id según el perfil del usuario
    tenant_id = None

    if usuario.rol.value == "administrador" and usuario.perfil_administrador:
        tenant_id = usuario.perfil_administrador.tenant_id

    elif usuario.rol.value == "mecanico" and usuario.perfil_mecanico:
        tenant_id = usuario.perfil_mecanico.tenant_id

    # 4. Generar Tokens
    token_data = {
        "sub": str(usuario.id), 
        "rol": rol_valor,
        "tenant_id": tenant_id, 
    }
    
    BitacoraService.registrar(
        db=db,
        accion="LOGIN",
        descripcion=f"Login exitoso: {usuario.username}",
        usuario_id=usuario.id,
    )

    return Token(
        access_token=crear_access_token(token_data),
        refresh_token=crear_refresh_token(token_data),
        token_type="bearer"
    )

# ============================================================
# SETUP TALLER (ONBOARDING ADMIN)
# ============================================================
@router.post(
    "/setup-taller",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RolUsuario.administrador))],
)
def setup_taller(
    datos: TallerCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_usuario),
):
    """
    Crea el taller del admin autenticado.
    (Se infiere onboarding por existencia de Taller asociado al Administrador.)
    """
    usuario = get_usuario_by_id(db, usuario_actual.id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 1) Asegurar perfil admin
    perfil_admin = db.query(Administrador).filter(Administrador.usuario_id == usuario.id).first()
    if not perfil_admin:
        perfil_admin = Administrador(usuario_id=usuario.id)
        db.add(perfil_admin)
        db.flush()

    rol_valor = usuario.rol.value if hasattr(usuario.rol, "value") else str(usuario.rol)

    # 2) Evitar duplicados — pero igual re-emitir tokens con el tenant actual
    #    (el JWT con el que llegó aquí fue emitido ANTES de tener tenant)
    existente = get_taller_by_admin(db, perfil_admin.id)
    if existente:
        token_data = {"sub": str(usuario.id), "rol": rol_valor, "tenant_id": existente.tenant_id}
        return {
            "message": "El taller ya estaba configurado",
            "taller_id": existente.id,
            "access_token": crear_access_token(token_data),
            "refresh_token": crear_refresh_token(token_data),
            "token_type": "bearer",
        }

    # 3) Crear taller (crea también su Tenant 1:1 y lo vincula al admin)
    nuevo_taller = crear_taller(db, perfil_admin.id, datos)

    # 4) CLAVE: devolver tokens NUEVOS con el tenant recién creado.
    #    Sin esto, el frontend seguiría usando el JWT viejo (tenant_id=null)
    #    y todos los endpoints con require_tenant (KPIs) devolverían 403.
    token_data = {"sub": str(usuario.id), "rol": rol_valor, "tenant_id": nuevo_taller.tenant_id}
    return {
        "message": "Taller configurado exitosamente",
        "taller_id": nuevo_taller.id,
        "access_token": crear_access_token(token_data),
        "refresh_token": crear_refresh_token(token_data),
        "token_type": "bearer",
    }


# Alias de compatibilidad (si algún frontend viejo lo usa)
@router.post(
    "/configurar-taller-solo",
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
    dependencies=[Depends(require_roles(RolUsuario.administrador))],
)
def configurar_taller_solo_compat(
    datos: TallerCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_usuario),
):
    return setup_taller(datos=datos, db=db, usuario_actual=usuario_actual)