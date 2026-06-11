
# Endpoints para que la app pueda:
# - Registrar su token FCM al usuario
# - Consultar sus notificaciones
# - Marcar notificaciones como leídas
# - Saber cuántas notificaciones tiene sin leer

# backend/app/routers/notificaciones.py
#
# Endpoints relacionados con notificaciones y tokens de dispositivo.
#
# Endpoints:
#   PUT  /notificaciones/push-token          → registrar/actualizar push token del dispositivo
#   GET  /notificaciones/mias                → listar notificaciones del usuario autenticado
#   PUT  /notificaciones/{id}/leer           → marcar una notificación como leída
#   PUT  /notificaciones/leer-todas          → marcar todas como leídas
#   GET  /notificaciones/no-leidas/conteo    → número de notificaciones no leídas (para badge)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.usuario import Usuario
from app.models.notificacion import Notificacion
from app.models.incidente import Incidente
from app.schemas.notificacion import NotificacionRead, PushTokenUpdate
from app.core.dependencies import get_current_usuario, get_current_administrador


router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


# ─── DEBUG: probar push al cliente de un incidente ───────────────────────────

@router.post("/test-push/incidente/{incidente_id}")
def probar_push_cliente(
    incidente_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Endpoint de DIAGNÓSTICO: envía una notificación de prueba al cliente
    del incidente y devuelve cada paso del proceso para depurar por qué
    no llegan los push a la app móvil.
    """
    from app.services import fcm_service
    from app.services.fcm_service import enviar_push_a_token

    diagnostico: dict = {"incidente_id": incidente_id}

    # 1. ¿Existe el incidente?
    incidente = db.query(Incidente).filter(Incidente.id == incidente_id).first()
    if not incidente:
        diagnostico["error"] = "Incidente no encontrado"
        return diagnostico

    # 2. ¿Tiene cliente?
    if not incidente.cliente:
        diagnostico["error"] = "El incidente no tiene cliente asociado"
        return diagnostico

    cliente_usuario = incidente.cliente.usuario
    diagnostico["cliente_id"] = incidente.cliente.id
    diagnostico["cliente_usuario_id"] = cliente_usuario.id if cliente_usuario else None
    diagnostico["cliente_nombre"] = (
        f"{cliente_usuario.nombre} {cliente_usuario.apellido}" if cliente_usuario else None
    )

    # 3. ¿Firebase está disponible e inicializado?
    diagnostico["firebase_admin_instalado"] = fcm_service._firebase_disponible
    diagnostico["firebase_inicializado"] = fcm_service._inicializar_firebase()

    # 4. ¿El cliente tiene push_token registrado?
    token = cliente_usuario.push_token if cliente_usuario else None
    diagnostico["tiene_push_token"] = bool(token)
    diagnostico["push_token_preview"] = f"{token[:25]}..." if token else None

    if not token:
        diagnostico["conclusion"] = (
            "EL CLIENTE NO TIENE push_token REGISTRADO. La app móvil debe llamar "
            "PUT /notificaciones/push-token al iniciar sesión con su token FCM. "
            "Verifica que Firebase esté configurado en la app Flutter y que el "
            "cliente haya iniciado sesión DESPUÉS de esa configuración."
        )
        return diagnostico

    if not diagnostico["firebase_inicializado"]:
        diagnostico["conclusion"] = (
            "FIREBASE NO ESTÁ INICIALIZADO en el backend. Verifica que el archivo "
            "de credenciales (firebase_credentials.json) exista y sea válido."
        )
        return diagnostico

    # 5. Enviar el push de prueba
    exito = enviar_push_a_token(
        token,
        "🔔 Notificación de prueba",
        f"Prueba de push para el incidente #{incidente_id}. Si ves esto, ¡funciona!",
        {"tipo": "test", "incidente_id": str(incidente_id)},
    )
    diagnostico["push_enviado"] = exito
    diagnostico["conclusion"] = (
        "PUSH ENVIADO CORRECTAMENTE a FCM. Si no llega al dispositivo: revisa que la "
        "app esté instalada con el mismo token, los permisos de notificación del "
        "teléfono, y que el token no sea de una instalación vieja (re-login ayuda)."
        if exito else
        "FCM RECHAZÓ EL ENVÍO. El token probablemente es inválido o expiró "
        "(app reinstalada). El cliente debe cerrar sesión y volver a entrar para "
        "registrar un token nuevo. Revisa los logs del backend para el error exacto."
    )
    return diagnostico


# ─── Registrar / actualizar token FCM del dispositivo ────────────────────────

@router.put("/push-token", status_code=status.HTTP_200_OK)
def registrar_push_token(
    datos: PushTokenUpdate,
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    """
    La app móvil o web llama a este endpoint al iniciar sesión,
    enviando el FCM token del dispositivo actual del usuario.
    El token se guarda en la tabla usuarios.push_token.
    """
    usuario.push_token = datos.push_token
    db.commit()
    return {"mensaje": "Push token registrado correctamente"}


# ─── Obtener notificaciones del usuario autenticado ──────────────────────────

@router.get("/mias", response_model=List[NotificacionRead])
def obtener_mis_notificaciones(
    limite: int = 30,
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    """
    Devuelve las últimas `limite` notificaciones del usuario autenticado,
    ordenadas de más reciente a más antigua.
    """
    notificaciones = (
        db.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario.id)
        .order_by(Notificacion.fecha_envio.desc())
        .limit(limite)
        .all()
    )
    return notificaciones


# ─── Conteo de notificaciones no leídas (para el badge en la app) ────────────

@router.get("/no-leidas/conteo")
def contar_no_leidas(
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    conteo = (
        db.query(Notificacion)
        .filter(
            Notificacion.usuario_id == usuario.id,
            Notificacion.leida == False
        )
        .count()
    )
    return {"no_leidas": conteo}


# ─── Marcar una notificación como leída ──────────────────────────────────────

@router.put("/{notificacion_id}/leer", status_code=status.HTTP_200_OK)
def marcar_como_leida(
    notificacion_id: int,
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    notif = (
        db.query(Notificacion)
        .filter(
            Notificacion.id == notificacion_id,
            Notificacion.usuario_id == usuario.id  # solo puede marcar las suyas
        )
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    notif.leida = True
    db.commit()
    return {"mensaje": "Notificación marcada como leída"}


# ─── Marcar TODAS las notificaciones del usuario como leídas ─────────────────

@router.put("/leer-todas", status_code=status.HTTP_200_OK)
def marcar_todas_como_leidas(
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    db.query(Notificacion).filter(
        Notificacion.usuario_id == usuario.id,
        Notificacion.leida == False
    ).update({"leida": True})
    db.commit()
    return {"mensaje": "Todas las notificaciones marcadas como leídas"}