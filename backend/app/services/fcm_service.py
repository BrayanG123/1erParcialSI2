# backend/app/services/fcm_service.py
#
# Servicio de comunicación con Firebase Cloud Messaging (FCM).
#
#Encapsula toda la comunicación con Firebase. Solo este archivo toca directamente `firebase-admin`. El resto del sistema usa este servicio sin necesitar saber los detalles de Firebase.
#
#
# Expone dos funciones:
#   - enviar_push_a_token(token, titulo, cuerpo, datos)
#       Envía una notificación a UN dispositivo específico.
#       Retorna True si fue enviada, False si falló.
#
#   - enviar_push_a_multiples(tokens, titulo, cuerpo, datos)
#       Envía a VARIOS dispositivos a la vez (máximo 500 por llamada, límite de Firebase).
#       Retorna un dict con success_count y failure_count.
#
# Inicialización:
#   Firebase Admin solo puede inicializarse UNA vez por proceso Python.
#   Usamos la variable _firebase_inicializado para evitar inicializar dos veces
#   si se llama a estas funciones desde múltiples endpoints.


import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Intentamos importar firebase_admin. Si no está instalado, el servicio
# retorna errores silenciosos en lugar de romper toda la app.
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    _firebase_disponible = True
except ImportError:
    _firebase_disponible = False
    logger.warning("firebase-admin no está instalado. Las notificaciones push están desactivadas.")

_firebase_inicializado = False


def _inicializar_firebase() -> bool:
    """
    Inicializa Firebase Admin SDK usando las credenciales del archivo JSON.
    Solo se ejecuta una vez aunque se llame múltiples veces.
    Retorna True si está inicializado correctamente, False si no.
    """
    global _firebase_inicializado

    if not _firebase_disponible:
        return False

    if _firebase_inicializado:
        return True

    # Verificar si ya fue inicializado por otro módulo (ej. en tests)
    if firebase_admin._apps:
        _firebase_inicializado = True
        return True

    try:
        from app.config import settings
        import os

        ruta_credenciales = settings.FIREBASE_CREDENTIALS_PATH

        # Buscar el archivo de credenciales relativo a la carpeta del backend
        if not os.path.isabs(ruta_credenciales):
            # Construir ruta absoluta desde la raíz del proyecto backend
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            ruta_credenciales = os.path.join(base_dir, ruta_credenciales)

        if not os.path.exists(ruta_credenciales):
            logger.error(
                f"Archivo de credenciales Firebase no encontrado: {ruta_credenciales}\n"
                "Descarga el archivo desde Firebase Console → Configuración → Cuentas de servicio."
            )
            return False

        cred = credentials.Certificate(ruta_credenciales)
        firebase_admin.initialize_app(cred)
        _firebase_inicializado = True
        logger.info("Firebase Admin SDK inicializado correctamente.")
        return True

    except Exception as e:
        logger.error(f"Error al inicializar Firebase: {e}")
        return False
    
def enviar_push_a_token(
    token: str,
    titulo: str,
    cuerpo: str,
    datos: Optional[dict] = None
) -> bool:
    """
    Envía una notificación push a un dispositivo específico.

    Parámetros:
        token:  FCM token del dispositivo destino.
        titulo: Título visible en la notificación.
        cuerpo: Texto del cuerpo de la notificación.
        datos:  Diccionario con metadatos extra (deben ser string:string).
                La app los usa para saber a qué pantalla navegar al tocar la notif.
                Ejemplo: {"tipo": "nuevo_incidente", "incidente_id": "15"}

    Retorna:
        True si Firebase confirmó el envío, False si hubo algún error.
    """
    if not token:
        logger.warning("enviar_push_a_token: token vacío, se omite el envío.")
        return False

    if not _inicializar_firebase():
        return False

    try:
        # FCM requiere que todos los valores del dict `data` sean strings
        datos_str = {str(k): str(v) for k, v in (datos or {}).items()}

        mensaje = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=cuerpo,
            ),
            data=datos_str,
            token=token,
            # Configuración Android: prioridad alta para notifs de emergencia
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    sound="default",
                    priority="high",
                )
            ),
            # Configuración APNS (iOS): también alta prioridad
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default")
                )
            ),
        )

        messaging.send(mensaje)
        logger.info(f"Push enviado correctamente a token: {token[:20]}...")
        return True

    except messaging.UnregisteredError:
        # El token ya no es válido (usuario desinstalió la app, etc.)
        logger.warning(f"Token FCM inválido o expirado: {token[:20]}...")
        return False
    except Exception as e:
        logger.error(f"Error al enviar push a token {token[:20]}...: {e}")
        return False
    
def enviar_push_a_multiples(
    tokens: list,
    titulo: str,
    cuerpo: str,
    datos: Optional[dict] = None
) -> dict:
    """
    Envía la misma notificación push a múltiples dispositivos a la vez.
    Más eficiente que llamar enviar_push_a_token() en un loop.

    Parámetros:
        tokens: Lista de FCM tokens de los dispositivos destino.
        titulo, cuerpo, datos: Igual que en enviar_push_a_token.

    Retorna:
        dict con claves "success" (envíos exitosos) y "failure" (fallidos).
    """
    if not tokens:
        return {"success": 0, "failure": 0}

    if not _inicializar_firebase():
        return {"success": 0, "failure": len(tokens)}

    try:
        datos_str = {str(k): str(v) for k, v in (datos or {}).items()}

        # Firebase permite máximo 500 tokens por llamada
        # Si hay más, partimos en lotes (unlikely en este proyecto)
        LOTE_MAX = 500
        total_success = 0
        total_failure = 0

        for i in range(0, len(tokens), LOTE_MAX):
            lote = tokens[i:i + LOTE_MAX]
            mensaje = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=titulo,
                    body=cuerpo,
                ),
                data=datos_str,
                tokens=lote,
                android=messaging.AndroidConfig(priority="high"),
            )

            respuesta = messaging.send_each_for_multicast(mensaje)
            total_success += respuesta.success_count
            total_failure += respuesta.failure_count

            logger.info(
                f"Push multicast: {respuesta.success_count} enviados, "
                f"{respuesta.failure_count} fallidos (lote {i//LOTE_MAX + 1})"
            )

        return {"success": total_success, "failure": total_failure}

    except Exception as e:
        logger.error(f"Error al enviar push multicast: {e}")
        return {"success": 0, "failure": len(tokens)}



