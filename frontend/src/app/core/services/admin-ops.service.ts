import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import {
  Bitacora_Evento,
  Comision_Servicio,
  Evidencia_Item,
  Pago_Request,
  Servicio_Realizado
} from '../models/admin-ops.model';

@Injectable({ providedIn: 'root' })
export class AdminOpsService {
  private http = inject(HttpClient);
  private readonly API_URL = environment.apiUrl;

  getServiciosRealizados() {
    return this.http.get<Servicio_Realizado[]>(`${this.API_URL}/servicios-realizados/`);
  }

  getAsignaciones() {
    return this.http.get<any[]>(`${this.API_URL}/asignaciones/`);
  }

  getEvidenciasPorIncidente(incidente_id: number) {
    return this.http.get<Evidencia_Item[]>(`${this.API_URL}/evidencias/incidente/${incidente_id}`);
  }

  getComisionPorServicio(servicio_id: number) {
    return this.http.get<Comision_Servicio>(`${this.API_URL}/comisiones/servicio/${servicio_id}`);
  }

  registrarPago(payload: Pago_Request) {
    return this.http.post(`${this.API_URL}/pagos/`, payload);
  }

  getPagos() {
    return this.http.get<any[]>(`${this.API_URL}/pagos/`);
  }

  getIncidentes() {
    return this.http.get<any[]>(`${this.API_URL}/incidentes/`);
  }

  getBitacoraAdmin() {
    return this.http.get<Bitacora_Evento[]>(`${this.API_URL}/admin/bitacora`);
  }

  getComisiones() {
    return this.http.get<Comision_Servicio[]>(`${this.API_URL}/comisiones/`);
  }


  getUsuariosAdmin() {
    return this.http.get<any[]>(`${this.API_URL}/admin/usuarios`);
  }

  createMecanico(datos: any) {
    return this.http.post<any>(`${this.API_URL}/admin/usuarios`, datos);
  }
  eliminarMecanico(usuario_id: number) {
    return this.http.delete(`${this.API_URL}/admin/usuarios/${usuario_id}`);
  }
}
