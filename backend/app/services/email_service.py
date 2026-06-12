"""
email_service.py — Envío de correos con adjuntos vía SMTP.

Usa SOLO la librería estándar de Python (smtplib + email): cero
dependencias nuevas.

CONFIGURACIÓN (en el .env del backend):
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=tucorreo@gmail.com
    SMTP_PASSWORD=xxxx xxxx xxxx xxxx   ← App Password de Google, NO tu contraseña
    SMTP_FROM=tucorreo@gmail.com        ← opcional (por defecto usa SMTP_USER)

CÓMO OBTENER EL APP PASSWORD DE GMAIL (resumen, detalle en REPORTES-EXPORTAR-CORREO.md):
    1. Activa la verificación en 2 pasos en tu cuenta Google
    2. https://myaccount.google.com/apppasswords → crear → copiar los 16 caracteres
"""
import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def smtp_configurado() -> bool:
    """True si hay credenciales SMTP en el .env."""
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def enviar_correo(
    destinatario: str,
    asunto: str,
    cuerpo: str,
    adjuntos: list[tuple[str, bytes, str]] | None = None,
) -> None:
    """
    Envía un correo con adjuntos opcionales.

    Parámetros:
        destinatario : email del receptor
        asunto       : subject del correo
        cuerpo       : texto plano del mensaje
        adjuntos     : lista de tuplas (nombre_archivo, contenido_bytes, mime_type)
                       ej: [("reporte.pdf", b"...", "application/pdf")]

    Lanza RuntimeError con mensaje claro si el SMTP no está configurado
    o si el servidor rechaza el envío.
    """
    if not smtp_configurado():
        raise RuntimeError(
            "El servidor de correo no está configurado. Agrega SMTP_HOST, "
            "SMTP_USER y SMTP_PASSWORD al .env del backend "
            "(ver REPORTES-EXPORTAR-CORREO.md para la guía con Gmail)."
        )

    # ── Armar el mensaje ──
    mensaje = EmailMessage()
    mensaje["From"] = settings.SMTP_FROM or settings.SMTP_USER
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    for nombre, contenido, mime in (adjuntos or []):
        # add_attachment necesita el MIME partido en tipo/subtipo
        maintype, _, subtype = mime.partition("/")
        mensaje.add_attachment(
            contenido,
            maintype=maintype,
            subtype=subtype or "octet-stream",
            filename=nombre,
        )

    # ── Conectar y enviar ──
    # Puerto 465 = SSL directo | Puerto 587 = STARTTLS (el estándar de Gmail)
    try:
        if settings.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                smtp.send_message(mensaje)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
                smtp.starttls()  # eleva la conexión a TLS (cifrada)
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                smtp.send_message(mensaje)
        logger.info(f"[Email] Correo enviado a {destinatario}: {asunto}")

    except smtplib.SMTPAuthenticationError:
        raise RuntimeError(
            "Gmail rechazó las credenciales. Verifica que SMTP_PASSWORD sea un "
            "App Password (16 caracteres) y no tu contraseña normal, y que la "
            "verificación en 2 pasos esté activa en la cuenta."
        )
    except (smtplib.SMTPException, OSError) as e:
        raise RuntimeError(f"No se pudo enviar el correo: {e}")
