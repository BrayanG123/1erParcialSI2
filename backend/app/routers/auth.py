from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.usuario import Token, UsuarioCreate, UsuarioRead, UsuarioConPerfil
from app.crud.usuario import (
    get_usuario_by_email,
    get_usuario_by_username,
    crear_usuario,
)
from app.core.security import verify_password, crear_access_token, crear_refresh_token, decodificar_token
from jose import JWTError



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
    
    return crear_usuario(db, datos)



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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Verificar que el usuario está activo
    if not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada"
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