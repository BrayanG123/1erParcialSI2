from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.config import settings


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """Convierte un password en texto plano a su hash argon2."""
    return pwd_context.hash(password)


def verify_password(password_plano: str, password_hash: str) -> bool:
    """Verifica si un password en texto plano coincide con su hash."""
    return pwd_context.verify(password_plano, password_hash)


# --- Tokens JWT ---

def crear_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Genera un JWT de acceso de corta duración.
    'data' debe contener al menos {"sub": str(usuario_id), "rol": rol}
    """
    payload = data.copy()

    if expires_delta:
        expira = datetime.now(timezone.utc) + expires_delta
    else:
        expira = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload.update({
        "exp": expira,
        "type": "access"
    })

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def crear_refresh_token(data: dict) -> str:
    """
    Genera un JWT de refresco de larga duración.
    Se usa solo para obtener nuevos access tokens.
    """
    payload = data.copy()
    expira = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload.update({
        "exp": expira,
        "type": "refresh"
    })

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> dict:
    """
    Decodifica y valida un JWT.
    Lanza JWTError si el token es inválido o expiró.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])