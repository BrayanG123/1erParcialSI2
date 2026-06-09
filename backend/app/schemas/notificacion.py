# backend/app/schemas/notificacion.py
#
# Define la forma de los datos que la API devuelve al cliente cuando consulta sus notificaciones.
#
# Schemas Pydantic para el endpoint GET /notificaciones/mias

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class NotificacionRead(BaseModel):
    """
    Datos que se devuelven al consultar notificaciones.
    El campo datos_extra es un JSON libre con metadatos (ej. incidente_id).
    """
    id: int
    titulo: str
    cuerpo: str
    canal: str
    destinatario_tipo: str
    estado: str
    leida: bool
    datos_extra: Optional[Any] = None
    fecha_envio: datetime

    model_config = {"from_attributes": True}


class PushTokenUpdate(BaseModel):
    """
    Body del endpoint PUT /usuarios/push-token.
    La app envía el token FCM del dispositivo actual.
    """
    push_token: str