from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import RolUsuario
from app.models.taller import Taller
from app.schemas.usuario import Token, UsuarioCreate, UsuarioRead, UsuarioConPerfil, AdminConTallerCreate
from app.crud.usuario import (
    get_usuario_by_email,
    get_usuario_by_username,
    crear_usuario,
)
from app.core.security import verify_password, crear_access_token, crear_refresh_token, decodificar_token, hash_password
from jose import JWTError
from app.services.bitacora import BitacoraService



router = APIRouter(
    prefix="/auth", 
    tags=["Autenticacion"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ============================================================
# REGISTRO
# =======================================================
@router.post(
    "/registro",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED
)
def registro(datos: UsuarioCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario con su perfil correspondiente."""
    if get_usuario_by_email(db, datos.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # Verificar que el username no esté en uso
    if get_usuario_by_username(db, datos.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El username ya está en uso"
        )
    
    nuevo = crear_usuario(db, datos)
    BitacoraService.registrar(
        db=db,
        accion="REGISTRO",
        descripcion=f"Nuevo usuario registrado: {nuevo.username} ({nuevo.rol})",
        usuario_id=nuevo.id
    )
    return nuevo



# ============================================================
# LOGIN
# ============================================================
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Autentica un usuario y retorna access + refresh token.
    El campo 'username' del formulario acepta el email del usuario.
    """

    # 1. Buscar el usuario por email
    usuario = get_usuario_by_email(db, form_data.username)

    # 2. Verificar que existe y que el password es correcto
    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        # Registrar en bitacora intento fallido (usuario_id puede ser None si no existe)
        BitacoraService.registrar(
            db=db,
            accion="LOGIN_FALLIDO",
            descripcion=f"Intento de login fallido para: {form_data.username}",
            usuario_id=usuario.id if usuario else None,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Verificar que el usuario está activo
    if not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada"
        )
    
    BitacoraService.registrar(
        db=db,
        accion="LOGIN",
        descripcion=f"Login exitoso: {usuario.username}",
        usuario_id=usuario.id,
    )
    
    # 4. Generar los tokens con el ID y rol del usuario
    token_data = {"sub": str(usuario.id), "rol": usuario.rol.value}

    return Token(
        access_token=crear_access_token(token_data),
        refresh_token=crear_refresh_token(token_data),
        token_type="bearer"
    )


# ============================================================
# REFRESH TOKEN
# ============================================================
@router.post("/refresh", response_model=Token)
def refresh(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Genera nuevos tokens usando un refresh token válido."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decodificar_token(token)

        # Verificar que sea refresh token, no access token
        if payload.get("type") != "refresh":
            raise credentials_exception

        usuario_id_str = payload.get("sub")
        if not usuario_id_str:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Verificar que el usuario sigue existiendo y activo
    from app.crud.usuario import get_usuario_by_id
    usuario = get_usuario_by_id(db, int(usuario_id_str))
    if not usuario or not usuario.is_active:
        raise credentials_exception

    # Generar nuevos tokens
    token_data = {"sub": str(usuario.id), "rol": usuario.rol.value}
    return Token(
        access_token=crear_access_token(token_data),
        refresh_token=crear_refresh_token(token_data),
        token_type="bearer"
    )


@router.post(
    "/registro-admin-taller",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED
)
def registro_admin_con_taller(datos: AdminConTallerCreate, db: Session = Depends(get_db)):
    """
    Registra un administrador junto con su taller en una sola operación.
    Ambos se crean en la misma transacción: si algo falla, no queda nada a medias.
    """
    if get_usuario_by_email(db, datos.email):
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    if get_usuario_by_username(db, datos.username):
        raise HTTPException(status_code=400, detail="El username ya está en uso")

    from app.models.usuario import Usuario, Administrador

    # 1. Crear el usuario base
    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        apellido=datos.apellido,
        email=datos.email,
        username=datos.username,
        password_hash=hash_password(datos.password),
        rol=RolUsuario.administrador,
    )
    db.add(nuevo_usuario)
    db.flush()   # genera el ID sin hacer commit aún

    # 2. Crear el perfil administrador
    perfil_admin = Administrador(usuario_id=nuevo_usuario.id)
    db.add(perfil_admin)
    db.flush()   # genera el ID del administrador

    # 3. Crear el taller vinculado al administrador
    taller = Taller(
        administrador_id=perfil_admin.id,
        nombre=datos.nombre_taller,
        direccion=datos.direccion_taller,
        telefono=datos.telefono_taller,
        latitud=datos.latitud_taller,
        longitud=datos.longitud_taller,
    )
    db.add(taller)
    db.commit()
    db.refresh(nuevo_usuario)

    BitacoraService.registrar(
        db=db,
        usuario_id=nuevo_usuario.id,
        accion="REGISTRO_ADMIN_TALLER",
        descripcion=f"Admin '{nuevo_usuario.username}' registrado con taller '{datos.nombre_taller}'",
    )
    return nuevo_usuario


# =======================================
# REGISTRO MECANICO
# =======================================
# @router.post("/registro/mecanico", response_model=UsuarioConPerfil, status_code=status.HTTP_201_CREATED)
# def registro_mecanico(datos: RegistroMecanicoRequest, db: Session = Depends(get_db)):
#     if get_usuario_by_email(db, datos.username):
#         raise HTTPException(status_code=400, detail="el email ya esta registrado")
#     if get_usuario_by_username(db, datos.username):
#         raise HTTPException(status_code=400, detail="El username ya está en uso")
#     nuevo = crear_usuario_mecanico(db, datos)
#     BitacoraService.registrar(
#         db=db,
#         accion="REGISTRO_MECANICO",
#         descripcion=f"Nuevo mecanico registrado: {nuevo.username}",
#         usuario_id=nuevo.id,
#     )

#     return nuevo