"""
websocket_manager.py

Versión 2 — Agrega almacenamiento en memoria de la última posición
conocida del mecánico por incidente.

Dos estructuras en memoria:
  conexiones_activas:   {incidente_id: [WebSocket, WebSocket, ...]}
  posiciones_mecanico:  {incidente_id: {"lat": float, "lng": float, "timestamp": str}}

La segunda estructura permite que un cliente que se conecta TARDE
pueda obtener la posición actual del mecánico sin esperar el próximo
ping de ubicación.
"""


import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Gestiona las conexiones WebSocket activas agrupadas por incidente.

    Uso:
        manager = ConnectionManager()

        # Al conectar:
        await manager.connect(incidente_id=42, websocket=ws)

        # Al desconectar:
        manager.disconnect(incidente_id=42, websocket=ws)

        # Para emitir un evento:
        await manager.broadcast(incidente_id=42, mensaje={"tipo": "estado", "estado": "en_camino"})
    """

    def __init__(self):
        # Clave: incidente_id → lista de WebSockets conectados (clientes y mecánico)
        self.conexiones_activas: Dict[int, List[WebSocket]] = {}

        # Clave: incidente_id → última posición conocida del mecánico
        # {"lat": float, "lng": float, "timestamp": str, "mecanico_id": int}
        self.posiciones_mecanico: Dict[int, dict] = {}

    
    # ─────────────────────────────────────────────────────────────────────────
    # GESTIÓN DE CONEXIONES
    # ─────────────────────────────────────────────────────────────────────────
    async def connect(self, incidente_id: int, websocket: WebSocket) -> None:
        """
        Acepta la conexión y la registra en el grupo del incidente.
        """
        await websocket.accept()

        if incidente_id not in self.conexiones_activas:
            self.conexiones_activas[incidente_id] = []

        self.conexiones_activas[incidente_id].append(websocket)

        cantidad = len(self.conexiones_activas[incidente_id])
        logger.info(f"[WS] Nueva conexión al incidente #{incidente_id}. Total: {cantidad}")


    def disconnect(self, incidente_id: int, websocket: WebSocket) -> None:
        """
        Elimina la conexión del grupo del incidente.
        Si el grupo queda vacío, elimina la clave del diccionario.
        """
        if incidente_id in self.conexiones_activas:
            try:
                self.conexiones_activas[incidente_id].remove(websocket)
            except ValueError:
                pass  # Ya estaba eliminado, ignorar

            # Limpiar el grupo si quedó vacío
            if not self.conexiones_activas[incidente_id]:
                del self.conexiones_activas[incidente_id]

        logger.info(f"[WS] Desconexión del incidente #{incidente_id}.")


    
    # ─────────────────────────────────────────────────────────────────────────
    # BROADCAST
    # ─────────────────────────────────────────────────────────────────────────
    async def broadcast(self, incidente_id: int, mensaje: dict) -> None:
        """
        Envía un mensaje JSON a TODOS los conectados al incidente.

        Si alguna conexión falla al enviar (cliente ya se fue sin avisar),
        la elimina silenciosamente.
        """
        if incidente_id not in self.conexiones_activas:
            return  # Nadie escucha, no hay que hacer nada

        conexiones = self.conexiones_activas[incidente_id].copy()
        fallidas = []

        for ws in conexiones:
            try:
                await ws.send_json(mensaje)
            except Exception as e:
                logger.warning(f"[WS] Falló envío al incidente #{incidente_id}: {e}")
                fallidas.append(ws)

        # Limpiar las conexiones que fallaron
        for ws in fallidas:
            self.disconnect(incidente_id, ws)

    async def broadcast_a_otros(
        self,
        incidente_id: int,
        mensaje: dict,
        excluir: WebSocket
    ) -> None:
        """
        Envía un mensaje a todos EXCEPTO al remitente.
        Útil para no devolver la ubicación al mecánico que la envió.
        """
        if incidente_id not in self.conexiones_activas:
            return

        conexiones = self.conexiones_activas[incidente_id].copy()
        fallidas = []

        for ws in conexiones:
            if ws is excluir:
                continue
            try:
                await ws.send_json(mensaje)
            except Exception as e:
                logger.warning(f"[WS] Falló envío (excluir) al incidente #{incidente_id}: {e}")
                fallidas.append(ws)

        for ws in fallidas:
            self.disconnect(incidente_id, ws)

    # ─────────────────────────────────────────────────────────────────────────
    # GESTIÓN DE POSICIONES DEL MECÁNICO
    # ─────────────────────────────────────────────────────────────────────────

    def guardar_posicion(
        self,
        incidente_id: int,
        lat: float,
        lng: float,
        mecanico_id: Optional[int] = None
    ) -> None:
        """
        Guarda la última posición conocida del mecánico para un incidente.
        Sobreescribe la posición anterior (solo guardamos la última).
        """
        self.posiciones_mecanico[incidente_id] = {
            "lat": lat,
            "lng": lng,
            "mecanico_id": mecanico_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_posicion(self, incidente_id: int) -> Optional[dict]:
        """
        Retorna la última posición conocida del mecánico.
        Retorna None si no hay posición guardada (mecánico aún no envió).
        """
        return self.posiciones_mecanico.get(incidente_id)

    def limpiar_posicion(self, incidente_id: int) -> None:
        """
        Elimina la posición guardada cuando el servicio finaliza.
        Llamar cuando el estado cambia a 'finalizado' o 'cancelado'.
        """
        if incidente_id in self.posiciones_mecanico:
            del self.posiciones_mecanico[incidente_id]
            logger.info(f"[WS] Posición limpiada para incidente #{incidente_id}")

        
    
    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────
    def get_cantidad_conectados(self, incidente_id: int) -> int:
        """Retorna cuántos clientes están conectados a un incidente."""
        return len(self.conexiones_activas.get(incidente_id, []))
    

# ── Instancia global compartida ────────────────────────────────────────────────
# Esta variable se importa desde cualquier router que necesite emitir eventos.
# Al ser una variable de módulo, Python la crea una sola vez.
manager = ConnectionManager()