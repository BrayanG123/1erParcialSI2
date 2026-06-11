import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment.development';
import { AsignacionRequest, AsignacionResponse } from '../models/asignacion.model';

@Injectable({ providedIn: 'root' })
export class AsignacionService {
  private http = inject(HttpClient);
  private readonly API_URL = `${environment.apiUrl}/asignaciones`;

  // Crear asignación (admin asigna mecánico a incidente)
  crearAsignacion(datos: AsignacionRequest) {
    return this.http.post<AsignacionResponse>(`${this.API_URL}/`, datos);
  }

  // Listar asignaciones del taller
  getAsignaciones() {
    return this.http.get<any[]>(`${this.API_URL}/`);
  }

  // Asignar (o reasignar) un mecánico a una asignación aceptada
  // Cambia estado a "taller_asignado" y notifica al cliente por push
  asignarMecanico(id: number, mecanicoId: number) {
    return this.http.patch<AsignacionResponse>(`${this.API_URL}/${id}/asignar-mecanico`, {
      mecanico_id: mecanicoId
    });
  }

  // Aceptar una asignación pendiente → cambia estado a "taller_asignado"
  // Esto notifica al cliente por push notification
  aceptarAsignacion(id: number) {
    return this.http.patch<AsignacionResponse>(`${this.API_URL}/${id}/aceptar`, {});
  }

  // Rechazar una asignación pendiente
  rechazarAsignacion(id: number, motivo: string) {
    return this.http.patch<AsignacionResponse>(`${this.API_URL}/${id}/rechazar`, {
      motivo_rechazo: motivo
    });
  }

  // Actualizar estado (usado por el mecánico: en_camino, en_atencion, finalizado)
  actualizarEstado(id: number, estado: string) {
    return this.http.patch(`${this.API_URL}/${id}/estado`, { estado });
  }

  // DEBUG: prueba de notificación push al cliente de un incidente.
  // Devuelve un diagnóstico paso a paso (token, firebase, resultado del envío).
  probarPushCliente(incidenteId: number) {
    return this.http.post<any>(
      `${environment.apiUrl}/notificaciones/test-push/incidente/${incidenteId}`, {}
    );
  }
}

