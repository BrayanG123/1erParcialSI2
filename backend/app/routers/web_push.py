# Dos endpoints:
# 1. `GET /web-push/vapid-public-key` → Angular pide la clave pública para suscribirse
# 2. `POST /web-push/suscribir` → Angular envía la suscripción del navegador al backend


# backend/app/routers/web_push.py
#
# Endpoints para la gestión de suscripciones Web Push.
#
# Flujo:
#   1. Angular hace GET /vapid-public-key → obtiene la clave pública VAPID
#   2. Angular usa esa clave para pedir al navegador una suscripción push
#   3. Angular envía la suscripción al backend via POST /suscribir
#   4. El backend la guarda en la tabla web_push_subscriptions
#   5. Cuando hay un nuevo incidente, el backend usa esa suscripción para enviar push

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.models.web_push_subscription import WebPushSubscription
from app.schemas.web_push import WebPushSubscriptionCreate, VapidPublicKeyResponse
from app.core.dependencies import get_current_usuario


router = APIRouter(prefix="/web-push", tags=["Web Push"])


@router.get("/vapid-public-key", response_model=VapidPublicKeyResponse)
def obtener_vapid_public_key():
    """
    Endpoint público (no requiere autenticación).
    Angular lo llama para obtener la clave pública VAPID
    antes de crear la suscripción del navegador.
    """
    from app.config import settings
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VAPID no está configurado en el servidor."
        )
    return {"vapid_public_key": settings.VAPID_PUBLIC_KEY}


@router.post("/suscribir", status_code=status.HTTP_201_CREATED)
def registrar_suscripcion(
    datos: WebPushSubscriptionCreate,
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    """
    Angular envía la suscripción del navegador cuando el usuario acepta las notificaciones.
    Si ya existe una suscripción con el mismo endpoint para este usuario, la actualiza.
    """
    # Verificar si ya existe esta suscripción para este usuario
    existente = db.query(WebPushSubscription).filter(
        WebPushSubscription.endpoint == datos.endpoint,
        WebPushSubscription.usuario_id == usuario.id
    ).first()

    if existente:
        # Actualizar las claves (pueden cambiar si el navegador renueva la suscripción)
        existente.p256dh = datos.p256dh
        existente.auth = datos.auth
    else:
        nueva = WebPushSubscription(
            endpoint=datos.endpoint,
            p256dh=datos.p256dh,
            auth=datos.auth,
            usuario_id=usuario.id,
        )
        db.add(nueva)

    db.commit()
    return {"mensaje": "Suscripción web push registrada correctamente"}


@router.delete("/desuscribir", status_code=status.HTTP_200_OK)
def eliminar_suscripcion(
    datos: WebPushSubscriptionCreate,
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    """
    El usuario desactiva las notificaciones push en el navegador.
    Angular envía la suscripción actual para que el backend la elimine.
    """
    db.query(WebPushSubscription).filter(
        WebPushSubscription.endpoint == datos.endpoint,
        WebPushSubscription.usuario_id == usuario.id
    ).delete()
    db.commit()
    return {"mensaje": "Suscripción eliminada"}