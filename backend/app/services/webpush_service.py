# Envía notificaciones usando el protocolo Web Push estándar con `pywebpush`. El resto del sistema llama a este servicio igual que llama a `fcm_service.py`.


# backend/app/services/webpush_service.py
#
# Servicio de Web Push para navegadores.
# Usa el protocolo estándar Web Push con VAPID para autenticar el servidor.
#
# Funciones:
#   enviar_web_push(suscripcion, titulo, cuerpo, datos)
#       Envía una notificación a UNA suscripción de navegador.
#
#   notificar_admins_nuevo_incidente_web(db, incidente_id)
#       Busca todas las suscripciones web de administradores y envía push.


import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


try:
    from pywebpush import webpush, WebPushException
    _webpush_disponible = True
except ImportError:
    _webpush_disponible = False
    logger.warning("pywebpush no está instalado. Web Push desactivado.")


def enviar_web_push(
    endpoint: str,
    p256dh: str,
    auth: str,
    titulo: str,
    cuerpo: str,
    datos: Optional[dict] = None,
) -> bool:
    """
    Envía una notificación Web Push a un navegador específico.

    El payload es un JSON que el Service Worker de Angular recibe y puede
    mostrar como notificación nativa del sistema operativo.

    Retorna True si el envío fue exitoso, False si falló.
    """
    if not _webpush_disponible:
        return False

    try:
        from app.config import settings

        # El payload es lo que el Service Worker recibe y muestra
        # 'notification' es el formato que ngsw (Angular Service Worker) entiende directamente
        payload = {
            "notification": {
                "title": titulo,
                "body": cuerpo,
                "icon": "/icons/icon-192x192.png",
                "data": datos or {},
                "requireInteraction": False,      # la notif no persiste hasta que el usuario la toque
                "vibrate": [200, 100, 200],
            }
        }

        webpush(
            subscription_info={
                "endpoint": endpoint,
                "keys": {
                    "p256dh": p256dh,
                    "auth": auth,
                }
            },
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={
                "sub": f"mailto:{settings.VAPID_CLAIM_EMAIL}"
            },
            content_encoding="aes128gcm",
        )

        logger.info(f"Web Push enviado correctamente a endpoint: {endpoint[:50]}...")
        return True

    except WebPushException as e:
        # 410 Gone o 404 = suscripción expirada/cancelada (usuario revocó el permiso)
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code in (404, 410):
                logger.info(f"Suscripción Web Push expirada (será eliminada): {endpoint[:50]}...")
                # Retornar código especial para indicar que hay que eliminar la suscripción
                return False
        logger.error(f"WebPushException: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado en Web Push: {e}")
        return False
    

def notificar_admins_nuevo_incidente_web(db, incidente_id: int) -> None:
    """
    Envía una notificación Web Push a todos los administradores que tienen
    suscripciones de navegador registradas.

    Se llama junto a notificar_admins_nuevo_incidente() (FCM) para cubrir
    tanto móvil como web.
    """
    from app.models.web_push_subscription import WebPushSubscription
    from app.models.usuario import Usuario, Administrador
    from app.models.notificacion import Notificacion

    # Buscar suscripciones de admins activos
    suscripciones = (
        db.query(WebPushSubscription)
        .join(Usuario, Usuario.id == WebPushSubscription.usuario_id)
        .join(Administrador, Administrador.usuario_id == Usuario.id)
        .filter(Usuario.is_active == True)
        .all()
    )

    if not suscripciones:
        logger.info(f"notificar_admins_web: ningún admin con suscripción web para incidente {incidente_id}")
        return

    titulo = "Nuevo incidente disponible"
    cuerpo = "Un cliente reportó una emergencia vehicular."
    datos = {
        "tipo": "nuevo_incidente",
        "incidente_id": str(incidente_id),
        "url": "/admin/incidentes"
    }

    suscripciones_a_eliminar = []

    for sub in suscripciones:
        exito = enviar_web_push(sub.endpoint, sub.p256dh, sub.auth, titulo, cuerpo, datos)

        if not exito:
            # Marcar para eliminar después del loop (no modificar la lista mientras iteramos)
            suscripciones_a_eliminar.append(sub.id)

        # Registrar en la tabla notificaciones
        notif = Notificacion(
            titulo=titulo,
            cuerpo=cuerpo,
            canal="push",
            destinatario_tipo="taller",
            estado="enviada" if exito else "fallida",
            datos_extra=datos,
            usuario_id=sub.usuario_id,
        )
        db.add(notif)

    # Eliminar suscripciones expiradas
    if suscripciones_a_eliminar:
        from app.models.web_push_subscription import WebPushSubscription
        db.query(WebPushSubscription).filter(
            WebPushSubscription.id.in_(suscripciones_a_eliminar)
        ).delete(synchronize_session=False)

    db.commit()
    logger.info(f"Web Push enviado a {len(suscripciones)} suscripciones para incidente {incidente_id}.")