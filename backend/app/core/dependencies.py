from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import get_db
from app.core.security import decodificar_token
from app.models.usuario import Usuario, RolUsuario
from app.crud.usuario import get_usuario_by_id


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ============================================================
# DEPENDENCIA BASE — cualquier usuario autenticado
# ============================================================
def get_current_usuario( token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
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
        Depends(require_roles(RolUsuario.admin))

        # Varios roles (cualquiera de ellos tiene acceso)
        Depends(require_roles(RolUsuario.cliente, RolUsuario.admin))
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


# DEPENDENCIAS LISTAS PARA USAR (atajos)
get_current_cliente = require_roles(RolUsuario.cliente)
get_current_mecanico = require_roles(RolUsuario.mecanico)
get_current_administrador = require_roles(RolUsuario.administrador)

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