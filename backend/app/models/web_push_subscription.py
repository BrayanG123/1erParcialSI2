# Guardar en base de datos la suscripción push de cada navegador. Un usuario puede tener múltiples suscripciones (un navegador en casa, otro en el trabajo). Cada suscripción tiene un `endpoint` único.

# backend/app/models/web_push_subscription.py
#
# Almacena las suscripciones Web Push de los navegadores.
# Un usuario puede tener múltiples suscripciones (varios navegadores/dispositivos).
#
# La suscripción contiene el endpoint y las claves de cifrado necesarias para
# enviar un mensaje push a ese navegador específico.


from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class WebPushSubscription(Base):
    __tablename__ = "web_push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    # El endpoint es la URL única del servidor push del navegador
    # Es el identificador principal de la suscripción
    endpoint = Column(Text, nullable=False)

    # Clave pública efímera del cliente (para cifrar el payload)
    p256dh = Column(Text, nullable=False)

    # Secreto de autenticación
    auth = Column(String(500), nullable=False)

    # Usuario al que pertenece esta suscripción
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False
    )

    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Evitar duplicados: el mismo endpoint solo puede registrarse una vez por usuario
    __table_args__ = (
        UniqueConstraint("endpoint", "usuario_id", name="uq_endpoint_usuario"),
    )

    usuario = relationship("Usuario")