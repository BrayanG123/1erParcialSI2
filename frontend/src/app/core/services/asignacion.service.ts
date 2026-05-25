import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment.development';
import { AsignacionRequest, AsignacionResponse } from '../models/asignacion.model';

@Injectable({ providedIn: 'root' })
export class AsignacionService {
  private http = inject(HttpClient);
  private readonly API_URL = `${environment.apiUrl}/asignaciones`;

  crearAsignacion(datos: AsignacionRequest) {
    return this.http.post<AsignacionResponse>(`${this.API_URL}/`, datos);
  }

  getAsignaciones() {
    return this.http.get<any[]>(`${this.API_URL}/`);
  }

  actualizarEstado(id: number, estado: string) {
    return this.http.patch(`${this.API_URL}/${id}`, { estado });
  }
}
