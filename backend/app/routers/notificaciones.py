
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
from app.schemas.notificacion import NotificacionRead, PushTokenUpdate
from app.core.dependencies import get_current_usuario


router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


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