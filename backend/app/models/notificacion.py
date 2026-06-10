# backend/app/models/notificacion.py
#
# Registrar en base de datos cada notificación enviada, con su estado y metadatos. Sirve para auditoría, para mostrar el historial de notificaciones al usuario, y para saber si fueron leídas.
# Representa cada notificación enviada o pendiente en el sistema.
# Se crea un registro por cada push que el backend intenta enviar.
#
# Campos importantes:
#   canal:              "push" o "websocket" — por dónde se envió
#   destinatario_tipo:  "cliente", "taller" o "mecanico"
#   estado:             "enviada", "fallida", "pendiente"
#   datos_extra:        JSON con metadatos (incidente_id, tipo de notif, etc.)
#   leida:              el usuario marcó la notificación como leída

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.models.base import Base


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)

    # Contenido visible de la notificación
    titulo = Column(String(200), nullable=False)
    cuerpo = Column(Text, nullable=False)

    # Clasificación del canal y destinatario
    canal = Column(String(20), default="push", nullable=False)       # push / websocket
    destinatario_tipo = Column(String(20), nullable=False)            # cliente / taller / mecanico

    # Estado de envío
    estado = Column(String(20), default="enviada", nullable=False)    # enviada / fallida / pendiente

    # Si el usuario ya la leyó (para el badge de notificaciones no leídas)
    leida = Column(Boolean, default=False, nullable=False)

    # Datos adicionales para que la app sepa a dónde navegar al tocarla
    # Ejemplo: {"tipo": "nuevo_incidente", "incidente_id": "15"}
    # Nota: los valores deben ser strings para compatibilidad con FCM
    datos_extra = Column(JSON, nullable=True)

    # A qué usuario pertenece esta notificación
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False
    )

    fecha_envio = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relación inversa hacia Usuario
    usuario = relationship("Usuario", back_populates="notificaciones")