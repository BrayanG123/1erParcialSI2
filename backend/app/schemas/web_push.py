from pydantic import BaseModel

class WebPushSubscriptionCreate(BaseModel):
    """
    Body que Angular envía cuando el usuario acepta las notificaciones push.
    Corresponde directamente al objeto PushSubscription del navegador.
    """
    endpoint: str
    p256dh: str
    auth: str


class VapidPublicKeyResponse(BaseModel):
    """Respuesta del endpoint GET /web-push/vapid-public-key"""
    vapid_public_key: str