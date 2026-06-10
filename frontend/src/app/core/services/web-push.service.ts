/*
Centraliza toda la lógica de Web Push en el frontend:
- Obtener la clave VAPID pública del backend
- Solicitar permiso y crear la suscripción del navegador
- Enviar la suscripción al backend para que el servidor pueda enviar push
- Escuchar mensajes push recibidos mientras el tab está abierto
*/

// frontend/src/app/core/services/web-push.service.ts
//
// Servicio singleton para Web Push Notifications en Angular.
//
// DEPENDENCIAS:
//   - SwPush: servicio de @angular/service-worker. Requiere que el SW esté activo.
//   - HttpClient: para comunicarse con el backend (obtener clave VAPID, registrar suscripción)
//
// USO:
//   Llamar suscribir() cuando el usuario hace clic en "Activar notificaciones".
//   Escuchar mensajesEntrantes$ para mostrar notificaciones en foreground.
//
// RESTRICCIÓN IMPORTANTE:
//   Web Push solo funciona cuando el Service Worker está activo.
//   El SW no está activo en ng serve (modo desarrollo).
//   Para probar: ng build → servir el build con http-server.


import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { SwPush } from '@angular/service-worker';
import { Observable, from, EMPTY } from 'rxjs';
import { catchError, switchMap, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment.development';


@Injectable({ providedIn: 'root' })
export class WebPushService {

  private http = inject(HttpClient);
  private swPush = inject(SwPush);

  private readonly BASE_URL = environment.apiUrl;

  // Observable que emite cuando llega un push mientras el tab está abierto
  // Los componentes pueden suscribirse para mostrar alertas en UI
  readonly mensajesEntrantes$ = this.swPush.messages;

  // ── Estado de la suscripción ────────────────────────────────────────────

  /**
   * Retorna true si el Service Worker está activo y el navegador
   * soporta notificaciones push.
   */
  get estaDisponible(): boolean {
    return this.swPush.isEnabled;
  }

   // ── Flujo principal ─────────────────────────────────────────────────────

  /**
   * Solicita permiso al usuario y crea la suscripción Web Push.
   * Si el usuario acepta, envía la suscripción al backend.
   *
   * Retorna un Observable que:
   * - Completa silenciosamente si todo sale bien
   * - Emite error si el usuario rechaza o hay un problema
   */
  suscribir(): Observable<void> {
    if (!this.estaDisponible) {
      console.warn('[WebPush] Service Worker no disponible. Ejecuta ng build para probar Web Push.');
      return EMPTY;
    }

    // 1. Obtener la clave VAPID pública del backend
    return this.http.get<{ vapid_public_key: string }>(`${this.BASE_URL}/web-push/vapid-public-key`).pipe(
      switchMap(({ vapid_public_key }) => {
        // 2. Pedir permiso al usuario y crear la suscripción usando la clave VAPID
        return from(
          this.swPush.requestSubscription({
            serverPublicKey: vapid_public_key
          })
        );
      }),
      switchMap((suscripcion: PushSubscription) => {
        // 3. Extraer los datos de la suscripción y enviarlos al backend
        const json = suscripcion.toJSON();
        const body = {
          endpoint: suscripcion.endpoint,
          p256dh: json.keys?.['p256dh'] ?? '',
          auth: json.keys?.['auth'] ?? '',
        };
        return this.http.post<void>(`${this.BASE_URL}/web-push/suscribir`, body);
      }),
      tap(() => {
        console.log('[WebPush] Suscripción registrada en el backend correctamente.');
        localStorage.setItem('webpush_suscrito', 'true');
      }),
      catchError(err => {
        console.error('[WebPush] Error al suscribirse:', err);
        return EMPTY;
      })
    );
  }

  /**
   * Cancela la suscripción actual y la elimina del backend.
   */
  desuscribir(): Observable<void> {
    return from(this.swPush.unsubscribe()).pipe(
      switchMap(() => {
        localStorage.removeItem('webpush_suscrito');
        console.log('[WebPush] Desuscrito correctamente.');
        // Idealmente también notificarías al backend, pero SwPush.unsubscribe()
        // no da acceso a la suscripción anterior. El backend eliminará la suscripción
        // automáticamente cuando intente enviar y reciba un 410 Gone.
        return EMPTY;
      }),
      catchError(err => {
        console.error('[WebPush] Error al desuscribirse:', err);
        return EMPTY;
      })
    );
  }

  /**
   * Verifica si el usuario ya tenía una suscripción activa
   * (guardada en localStorage en una sesión anterior).
   */
  get yaSuscrito(): boolean {
    return localStorage.getItem('webpush_suscrito') === 'true';
  }

}
