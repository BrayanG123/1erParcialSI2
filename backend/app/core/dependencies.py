from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jwt import PyJWTError as JWTError

from app.database import get_db
from app.core.security import decodificar_token
from app.models.usuario import Usuario, RolUsuario
from app.crud.usuario import get_usuario_by_id


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ============================================================
# DEPENDENCIA BASE — cualquier usuario autenticado
# ============================================================
def get_current_usuario( 
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Extrae el token del header Authorization, lo valida
    y retorna el usuario autenticado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 1. Decodificar el token
        payload = decodificar_token(token)
        # 2. Verificar que sea un access token (no un refresh token)
        if payload.get("type") != "access":
            raise credentials_exception

        # 3. Obtener el ID del usuario del payload
        usuario_id_str: str = payload.get("sub")
        if usuario_id_str is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # 4. Buscar el usuario en la base de datos
    usuario = get_usuario_by_id(db, int(usuario_id_str))
    if not usuario:
        raise credentials_exception

    # 5. Verificar que el usuario está activo
    if not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada"
        )

    return usuario

# FÁBRICA DE DEPENDENCIAS POR ROL(ES)
def require_roles(*roles: RolUsuario):
    """
    Fábrica que genera una dependencia para uno o varios roles.

    Uso:
        # Un solo rol
        Depends(require_roles(RolUsuario.administrador))

        # Varios roles (cualquiera de ellos tiene acceso)
        Depends(require_roles(RolUsuario.cliente, RolUsuario.administrador))
    """
    def dependencia(usuario: Usuario = Depends(get_current_usuario)) -> Usuario:
        if usuario.rol not in roles:
            roles_str = ", ".join(r.value for r in roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso restringido a: {roles_str}"
            )
        return usuario
    return dependencia

# ============================================================
# SHORTCUTS POR ROL — conveniencia para los routers
# ============================================================
def get_current_superadmin(
    usuario: Usuario = Depends(get_current_usuario)
) -> Usuario:
    """Shortcut: solo permite superadmin."""
    if usuario.rol != RolUsuario.superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a superadmin"
        )
    return usuario

def get_current_administrador(
    usuario: Usuario = Depends(get_current_usuario)
) -> Usuario:
    """Shortcut: solo permite administrador."""
    if usuario.rol != RolUsuario.administrador:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a administrador"
        )
    return usuario

def get_current_mecanico(
    usuario: Usuario = Depends(get_current_usuario)
) -> Usuario:
    """Shortcut: solo permite mecanico."""
    if usuario.rol != RolUsuario.mecanico:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a mecanico"
        )
    return usuario

def get_current_cliente(
    usuario: Usuario = Depends(get_current_usuario)
) -> Usuario:
    if usuario.rol != RolUsuario.cliente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a cliente"
        )
    return usuario

def get_cliente_o_admin(
    usuario: Usuario = Depends(get_current_usuario)
) -> Usuario:
    """
    Permite acceso tanto a clientes como a administradores.
    Usado en pagos: el cliente puede iniciar el pago, el admin puede confirmarlo.
    """
    if usuario.rol not in (RolUsuario.cliente, RolUsuario.administrador):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a cliente o administrador"
        )
    return usuario


# ============================================================
# DEPENDENCIAS DE TENANT  
# ============================================================

def get_tenant_id_opcional(token: str = Depends(oauth2_scheme)) -> Optional[int]:
    """
    Extrae el tenant_id del JWT sin lanzar error si es None.

    Útil para endpoints que el superadmin también puede usar
    (sin tenant) o donde el tenant es opcional para el filtro.

    Retorna:
        int  → si el usuario tiene tenant asignado
        None → si es superadmin, cliente, o el perfil no tiene tenant aún
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decodificar_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return payload.get("tenant_id")  # puede ser None


def require_tenant(
    tenant_id: Optional[int] = Depends(get_tenant_id_opcional),
) -> int:
    """
    Igual que get_tenant_id_opcional pero lanza 403 si el tenant es None.

    Usar en endpoints que SOLO deben responder a usuarios con tenant asignado
    (administradores y mecánicos operativos).

    Uso en un endpoint:
        @router.get("/mis-talleres/")
        def listar(
            tenant_id: int = Depends(require_tenant),
            db: Session = Depends(get_db)
        ):
            return db.query(Taller).filter(Taller.tenant_id == tenant_id).all()
    """
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este recurso requiere un tenant asignado. "
                   "Tu cuenta no tiene una organización vinculada.",
        )
    return tenant_id

# DEPENDENCIAS LISTAS PARA USAR (atajos)
get_current_cliente = require_roles(RolUsuario.cliente)
get_current_mecanico = require_roles(RolUsuario.mecanico)
get_current_administrador = require_roles(RolUsuario.administrador)
get_current_superadmin = require_roles(RolUsuario.superadmin)

# combinaciones utiles para este proyecto
get_cliente_o_admin = require_roles(RolUsuario.cliente, RolUsuario.administrador)
get_mecanico_o_admin = require_roles(RolUsuario.mecanico, RolUsuario.administrador)



# ============================================================
# DEPENDENCIAS POR ROL
# ============================================================
# def get_current_cliente(
#     usuario: Usuario = Depends(get_current_usuario)
# ) -> Usuario:
#     """Solo permite acceso a usuarios con rol cliente."""
#     if usuario.rol != RolUsuario.cliente:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Acceso restringido a clientes"
#         )
#     return usuario

# def get_current_mecanico(
#     usuario: Usuario = Depends(get_current_usuario)
# ) -> Usuario:
#     """Solo permite acceso a usuarios con rol mecánico."""
#     if usuario.rol != RolUsuario.mecanico:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Acceso restringido a mecánicos"
#         )
#     return usuario


# def get_current_admin(
#     usuario: Usuario = Depends(get_current_usuario)
# ) -> Usuario:
#     """Solo permite acceso a usuarios con rol administrador."""
#     if usuario.rol != RolUsuario.administrador:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Acceso restringido a administradores"
#         )
#     return usuario


# def get_current_usuario_activo(
#     usuario: Usuario = Depends(get_current_usuario)
# ) -> Usuario:
#     """Cualquier usuario autenticado sin importar el rol."""
#     return usuario