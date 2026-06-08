/**
 * websocket.service.ts
 *
 * Servicio singleton que gestiona UNA conexión WebSocket activa a la vez.
 *
 * El componente llama a `conectar(incidente_id)` al seleccionar una asignación
 * y a `desconectar()` al destruirse o cambiar de asignación.
 *
 * Los mensajes del servidor se publican en un Subject<any> que el componente
 * puede escuchar suscribiéndose a `mensajes$`.
 */


import { Injectable, OnDestroy } from '@angular/core';
import { Subject, Observable } from 'rxjs';
import { environment } from '../../../environments/environment.development';

@Injectable({ providedIn: 'root' })
export class WebSocketService implements OnDestroy {

  // Canal de mensajes entrantes.
  // El componente se suscribe a este observable para reaccionar a los mensajes.
  private _mensajes$ = new Subject<any>();

  // Referencia a la conexión WebSocket activa (o null si no hay ninguna)
  private ws: WebSocket | null = null;

  // ID del incidente al que está conectado actualmente (para evitar reconexiones innecesarias)
  private incidente_activo: number | null = null;

  // Estado público de la conexión
  estado: 'desconectado' | 'conectando' | 'conectado' | 'error' = 'desconectado';

  // Observable público que el componente consume
  get mensajes$(): Observable<any> {
    return this._mensajes$.asObservable();
  }

  /**
   * Abre una conexión WebSocket hacia el incidente indicado.
   * Si ya hay una conexión abierta para ese mismo incidente, no hace nada.
   * Si hay una conexión a otro incidente, la cierra primero.
   *
   * @param incidente_id  ID del incidente a seguir
   * @param rol           'cliente' (por defecto) o 'mecanico'
   * @param mecanico_id   Solo necesario si rol === 'mecanico'
   */
  conectar(
    incidente_id: number,
    rol: string = 'cliente',
    mecanico_id?: number
  ): void {
    // Si ya estamos conectados al mismo incidente, no hacer nada
    if (this.ws && this.incidente_activo === incidente_id) {
      return;
    }

    // Cerrar conexión anterior si existe
    this.desconectar();

    // Construir URL con query params
    let url = `${environment.wsUrl}/ws/incidente/${incidente_id}?rol=${rol}`;
    if (mecanico_id !== undefined) {
      url += `&mecanico_id=${mecanico_id}`;
    }

    console.log(`[WS Service] Conectando a: ${url}`);
    this.estado = 'conectando';
    this.incidente_activo = incidente_id;

    this.ws = new WebSocket(url);

    // ── Al conectar exitosamente ───────────────────────────────────────────
    this.ws.onopen = () => {
      console.log(`[WS Service] Conectado al incidente #${incidente_id}`);
      this.estado = 'conectado';
    };

    // ── Al recibir un mensaje ──────────────────────────────────────────────
    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        this._mensajes$.next(data);
      } catch (e) {
        console.warn('[WS Service] No se pudo parsear el mensaje:', event.data);
      }
    };

    // ── Al desconectarse ──────────────────────────────────────────────────
    this.ws.onclose = (event) => {
      console.log(`[WS Service] Conexión cerrada. Código: ${event.code}`);
      this.estado = 'desconectado';
      this.incidente_activo = null;
      this.ws = null;
    };

    // ── Si hay un error ───────────────────────────────────────────────────
    this.ws.onerror = (error) => {
      console.error('[WS Service] Error de WebSocket:', error);
      this.estado = 'error';
    };
  }

  /**
   * Envía un mensaje JSON al servidor por el WebSocket activo.
   * No hace nada si no hay conexión abierta.
   */
  enviarMensaje(mensaje: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(mensaje));
    } else {
      console.warn('[WS Service] No hay conexión abierta para enviar mensajes.');
    }
  }

  /**
   * Cierra la conexión WebSocket activa.
   * Llamar desde ngOnDestroy del componente o al navegar a otra página.
   */
  desconectar(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.incidente_activo = null;
      this.estado = 'desconectado';
      console.log('[WS Service] Desconectado manualmente.');
    }
  }

  // Angular llama esto cuando el servicio se destruye (al cerrar la app)
  ngOnDestroy(): void {
    this.desconectar();
  }
}
