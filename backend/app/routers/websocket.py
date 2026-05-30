"""
websocket.py

Este router expone dos endpoints:

1. WS  ws://localhost:8000/ws/incidente/{incidente_id}
   — Los clientes (app Angular, Flutter) se conectan aquí para escuchar eventos.
   — El servidor queda esperando mensajes (el cliente puede enviar su ubicación GPS).
   — Cuando el cliente se desconecta, se limpia la conexión.

2. POST /ws/emitir/{incidente_id}
   — Endpoint REST interno para que otros routers (como asignacion_servicio.py)
     puedan emitir eventos sin conocer los detalles del manager.
   — No es llamado por el frontend: es llamado por el backend mismo.


Versión 2 — Agrega:
  1. Query param ?rol=mecanico para identificar quién se conecta
  2. Manejo especial de mensajes de ubicación del mecánico
  3. Endpoint REST GET /ws/posicion/{incidente_id} para obtener
     la última posición del mecánico al conectarse por primera vez
  4. Limpieza de posición cuando el servicio finaliza
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel

from app.services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT WEBSOCKET PRINCIPAL
# Los clientes se conectan aquí al abrir la pantalla de tracking
# ─────────────────────────────────────────────────────────────────────────────

@router.websocket("/ws/incidente/{incidente_id}")
async def websocket_incidente(
    incidente_id: int,
    websocket: WebSocket,
    rol: Optional[str] = Query(default="cliente"),
    mecanico_id: Optional[int] = Query(default=None),
):
    """
    Endpoint WebSocket para tracking de un incidente específico.

   Query params opcionales:
        ?rol=mecanico       — indica que quien se conecta es el mecánico
        ?mecanico_id=3      — id del mecánico (para registrar en la posición)

    Ejemplos de URLs:
        Cliente:  ws://localhost:8000/ws/incidente/42
        Mecánico: ws://localhost:8000/ws/incidente/42?rol=mecanico&mecanico_id=3

    Mensajes que el cliente puede enviar:
        {"tipo": "ping"}
        → Respuesta: {"tipo": "pong"}

    Mensajes que el mecánico puede enviar:
        {"tipo": "ubicacion", "lat": -17.39, "lng": -66.15}
        → El servidor guarda la posición y hace broadcast a los demás

    Mensajes que el servidor emite (broadcast a todos):
        {"tipo": "cambio_estado", "estado": "en_camino", ...}   ← desde asignacion_servicio.py
        {"tipo": "ubicacion_mecanico", "lat": ..., "lng": ...}  ← desde este mismo endpoint
        {"tipo": "conexion_exitosa", ...}                        ← al conectarse
    """
    await manager.connect(incidente_id, websocket)
    es_mecanico = (rol == "mecanico")

    try:
        # Mensaje de bienvenida con info útil
        bienvenida = {
            "tipo": "conexion_exitosa",
            "incidente_id": incidente_id,
            "rol": rol,
            "conectados": manager.get_cantidad_conectados(incidente_id),
        }

        # Si hay una posición guardada del mecánico, incluirla en la bienvenida
        # Esto permite que el cliente vea el marcador desde el primer momento
        posicion_actual = manager.get_posicion(incidente_id)
        if posicion_actual:
            bienvenida["ultima_posicion_mecanico"] = posicion_actual

        await websocket.send_json(bienvenida)

        # Bucle principal: esperar mensajes
        while True:
            data = await websocket.receive_json()
            tipo = data.get("tipo")

            # ── Ubicación GPS enviada por el mecánico ─────────────────────────
            if tipo == "ubicacion" and es_mecanico:
                lat = data.get("lat")
                lng = data.get("lng")

                # Validación básica
                if lat is None or lng is None:
                    await websocket.send_json({
                        "tipo": "error",
                        "mensaje": "El mensaje de ubicación debe incluir 'lat' y 'lng'"
                    })
                    continue

                # Guardar en memoria (sobreescribe la anterior)
                manager.guardar_posicion(
                    incidente_id=incidente_id,
                    lat=lat,
                    lng=lng,
                    mecanico_id=mecanico_id,
                )

                # Redistribuir a TODOS MENOS al mecánico que envió
                await manager.broadcast_a_otros(
                    incidente_id=incidente_id,
                    mensaje={
                        "tipo": "ubicacion_mecanico",
                        "lat": lat,
                        "lng": lng,
                        "mecanico_id": mecanico_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    excluir=websocket,
                )

            # ── Ping / keepalive ───────────────────────────────────────────────
            elif tipo == "ping":
                await websocket.send_json({
                    "tipo": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            # ── Mensaje desconocido ────────────────────────────────────────────
            else:
                logger.debug(f"[WS] Mensaje no manejado en incidente #{incidente_id}: {tipo}")

    except WebSocketDisconnect:
        manager.disconnect(incidente_id, websocket)
        logger.info(f"[WS] {'Mecánico' if es_mecanico else 'Cliente'} desconectado del incidente #{incidente_id}")

    except Exception as e:
        logger.error(f"[WS] Error en incidente #{incidente_id}: {e}")
        manager.disconnect(incidente_id, websocket)



# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT REST — obtener última posición del mecánico
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/ws/posicion/{incidente_id}")
async def get_posicion_mecanico(incidente_id: int):
    """
    Retorna la última posición conocida del mecánico para un incidente.

    Uso: El cliente Angular/Flutter llama a este endpoint al cargar
    la pantalla de tracking (antes de conectarse al WebSocket) para
    mostrar el marcador del mecánico desde el primer momento, sin
    esperar el próximo ping de ubicación.

    Retorna 404 si el mecánico aún no ha enviado ninguna posición.
    """
    posicion = manager.get_posicion(incidente_id)

    if posicion is None:
        raise HTTPException(
            status_code=404,
            detail="El mecánico aún no ha enviado su posición o el servicio no está activo."
        )

    return {
        "incidente_id": incidente_id,
        "posicion": posicion,
    }



# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT REST AUXILIAR — para emitir eventos desde otros routers
# ─────────────────────────────────────────────────────────────────────────────

class EventoWS(BaseModel):
    """
    Estructura del evento que se emite a los clientes conectados.
    """
    tipo: str           # "cambio_estado", "ubicacion_mecanico", etc.
    estado: str | None = None
    mensaje: str | None = None
    datos: dict | None = None  # datos adicionales (mecánico, taller, etc.)


@router.post("/ws/emitir/{incidente_id}", status_code=200)
async def emitir_evento(incidente_id: int, evento: EventoWS):
    """
    Endpoint REST interno para emitir un evento WebSocket a todos
    los clientes conectados a un incidente.

    Este endpoint NO es para el frontend. Es para que otros routers
    del mismo backend puedan emitir eventos sin importar directamente el manager.

    Ejemplo de uso interno:
        import httpx
        # o simplemente llamando a manager.broadcast() directamente
    """
    cantidad = manager.get_cantidad_conectados(incidente_id)

    await manager.broadcast(incidente_id, {
        "tipo": evento.tipo,
        "estado": evento.estado,
        "mensaje": evento.mensaje,
        "datos": evento.datos,
        "incidente_id": incidente_id,
    })

    return {
        "ok": True,
        "incidente_id": incidente_id,
        "clientes_notificados": cantidad
    }