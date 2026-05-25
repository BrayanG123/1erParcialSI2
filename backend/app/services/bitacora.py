from sqlalchemy.orm import Session
from app.models.bitacora import Bitacora

class BitacoraService:

    @staticmethod
    def registrar(
        db: Session,
        accion: str,
        descripcion: str = None,
        usuario_id: int = None,
        ip_address: str = None,
    ) -> Bitacora:
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
        return (
            db.query(Bitacora)
            .filter(Bitacora.usuario_id == usuario_id)
            .order_by(Bitacora.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def obtener_por_usuarios(
        db: Session,
        usuario_ids: list[int],
        skip: int = 0,
        limit: int = 50,
    ) -> list[Bitacora]:
        """Retorna eventos de una lista de usuarios (para aislar bitácora por taller)."""
        return (
            db.query(Bitacora)
            .filter(Bitacora.usuario_id.in_(usuario_ids))
            .order_by(Bitacora.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )