# backend/app/services/notificacion_service.py
#
#Lógica de negocio de las notificaciones. Sabe a quién notificar según el evento del sistema. El router no debería contener esta lógica — la delega a este servicio.
#
# Capa de lógica de negocio para las notificaciones.
#
# Funciones:
#   - notificar_admins_nuevo_incidente(db, incidente_id)
#       Busca todos los administradores con push_token registrado
#       y les envía una notificación de nuevo incidente disponible.
#
#   - notificar_cliente_cambio_estado(db, cliente_usuario_id, incidente_id, mensaje)
#       Envía al cliente una notificación con el nuevo estado de su incidente.
#
# Cada función también guarda un registro en la tabla `notificaciones`.

import logging
from sqlalchemy.orm import Session

from app.models.notificacion import Notificacion
from app.models.usuario import Usuario, Administrador
from app.services.fcm_service import enviar_push_a_multiples, enviar_push_a_token

logger = logging.getLogger(__name__)


def notificar_admins_nuevo_incidente(db: Session, incidente_id: int) -> None:
    """
    Se llama cuando un cliente crea un nuevo incidente.

    Busca todos los administradores de taller que tengan push_token registrado
    y les envía una notificación push. También registra en BD cada envío.

    Por ahora notifica a TODOS los admins (versión simple para el examen).
    En una versión más avanzada se filtraría por distancia y especialidad del taller.
    """
    # Buscar usuarios con rol administrador que tengan token FCM
    admins_con_token = (
        db.query(Usuario)
        .join(Administrador, Administrador.usuario_id == Usuario.id)
        .filter(
            Usuario.push_token.isnot(None),
            Usuario.is_active == True
        )
        .all()
    )

    if not admins_con_token:
        logger.info(f"notificar_admins_nuevo_incidente: ningún admin con push_token para incidente {incidente_id}")
        return

    tokens = [u.push_token for u in admins_con_token]
    titulo = "Nuevo incidente disponible"
    cuerpo = "Un cliente reportó una emergencia vehicular. Revisa los incidentes disponibles."
    datos = {
        "tipo": "nuevo_incidente",
        "incidente_id": str(incidente_id),
    }

    resultado = enviar_push_a_multiples(tokens, titulo, cuerpo, datos)
    estado_envio = "enviada" if resultado["success"] > 0 else "fallida"

    # Registrar en BD un registro por cada admin notificado
    for admin in admins_con_token:
        notif = Notificacion(
            titulo=titulo,
            cuerpo=cuerpo,
            canal="push",
            destinatario_tipo="taller",
            estado=estado_envio,
            datos_extra=datos,
            usuario_id=admin.id,
        )
        db.add(notif)

    db.commit()
    logger.info(
        f"Notificación de nuevo incidente {incidente_id} enviada a {len(admins_con_token)} admins. "
        f"Exitosas: {resultado['success']}, Fallidas: {resultado['failure']}"
    )


def notificar_cliente_cambio_estado(
    db: Session,
    cliente_usuario_id: int,
    incidente_id: int,
    mensaje: str,
    tipo: str = "estado_asignacion"
) -> None:
    """
    Se llama cuando el estado del incidente/asignación cambia.

    Envía al cliente una notificación push con el mensaje del nuevo estado.
    Registra el envío en la tabla notificaciones.

    Parámetros:
        cliente_usuario_id: ID del usuario (tabla usuarios) del cliente.
        incidente_id:       ID del incidente afectado.
        mensaje:            Texto descriptivo del cambio de estado.
        tipo:               Tipo de notificación para que la app sepa a dónde navegar.
    """
    usuario = db.query(Usuario).filter(Usuario.id == cliente_usuario_id).first()

    if not usuario:
        logger.warning(f"notificar_cliente: usuario {cliente_usuario_id} no encontrado")
        return

    datos = {
        "tipo": tipo,
        "incidente_id": str(incidente_id),
    }

    titulo = "Actualización de tu incidente"
    exito = False

    if usuario.push_token:
        exito = enviar_push_a_token(usuario.push_token, titulo, mensaje, datos)
    else:
        logger.info(f"notificar_cliente: usuario {cliente_usuario_id} no tiene push_token registrado")

    # Registrar siempre en BD aunque no haya token (para auditoría y vista in-app)
    notif = Notificacion(
        titulo=titulo,
        cuerpo=mensaje,
        canal="push",
        destinatario_tipo="cliente",
        estado="enviada" if exito else ("pendiente" if not usuario.push_token else "fallida"),
        datos_extra=datos,
        usuario_id=cliente_usuario_id,
    )
    db.add(notif)
    db.commit()