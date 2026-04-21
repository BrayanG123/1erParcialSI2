from sqlalchemy.orm import Session

from app.models.evidencia import Evidencia
from app.schemas.evidencia import EvidenciaCreate



def crear_evidencia(db: Session, datos: EvidenciaCreate) -> Evidencia:
    evidencia = Evidencia(
        incidente_id=datos.incidente_id,
        tipo=datos.tipo,
        url_archivo=datos.url_archivo,
    )
    db.add(evidencia)
    db.commit()
    db.refresh(evidencia)
    return evidencia


def get_evidencias_de_incidente(db: Session, incidente_id: int) -> list[Evidencia]:
    return (
        db.query(Evidencia)
        .filter(Evidencia.incidente_id == incidente_id)
        .order_by(Evidencia.fecha_subida)
        .all()
    )


def get_evidencias_sin_procesar(db: Session) -> list[Evidencia]:
    """Para que la IA sepa qué evidencias procesar (lección 23)."""
    return db.query(Evidencia).filter(Evidencia.procesado_ia == 0).all()


def marcar_evidencia_procesada(db: Session, evidencia_id: int) -> None:
    db.query(Evidencia).filter(Evidencia.id == evidencia_id).update(
        {"procesado_ia": 1}
    )
    db.commit()