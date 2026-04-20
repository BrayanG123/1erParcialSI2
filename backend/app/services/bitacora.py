from sqlalchemy.orm import Session
from app.models.bitacora import Bitacora


class BitacoraService:
    """Servicio para registrar eventos de auditoría en la bitácora."""

    @staticmethod
    def registrar(
        db: Session,
        accion: str,
        descripcion: str = None,
        usuario_id: int = None,
        ip_address: str = None,
    ) -> Bitacora:
        """
        Registra un evento en la bitácora.

        Args:
            db: sesión de base de datos
            accion: código de la acción (ej: "LOGIN", "REGISTRO_CLIENTE")
            descripcion: texto legible del evento
            usuario_id: ID del usuario relacionado (opcional)
            ip_address: IP del cliente (opcional)
        """
        entrada = Bitacora(
            accion=accion,
            descripcion=descripcion,
            usuario_id=usuario_id,
            ip_address=ip_address,
        )
        db.add(entrada)
        db.commit()
        db.refresh(entrada)
        return entrada
    
    @staticmethod
    def obtener_todos(
        db: Session,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Bitacora]:
        """Retorna los últimos eventos registrados, del más reciente al más antiguo."""
        return (
            db.query(Bitacora)
            .order_by(Bitacora.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def obtener_por_usuario(
        db: Session,
        usuario_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Bitacora]:
        """Retorna los eventos de un usuario específico."""
        return (
            db.query(Bitacora)
            .filter(Bitacora.usuario_id == usuario_id)
            .order_by(Bitacora.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )