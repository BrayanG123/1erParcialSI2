import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { SuperadminKpis } from '../models/superadmin.model';
import { TallerGlobalRow } from '../../features/talleres/models/taller.model';
import { Usuario } from '../../features/usuarios/models/usuario.model';

@Injectable({ providedIn: 'root' })
export class SuperadminService {
  private http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/superadmin`;

  getKpis() {
    return this.http.get<SuperadminKpis>(`${this.baseUrl}/kpis`);
  }

  getTalleres() {
    return this.http.get<TallerGlobalRow[]>(`${this.baseUrl}/talleres`);
  }

  updateTaller(id: number, data: any) {
    return this.http.patch(`${this.baseUrl}/talleres/${id}`, data);
  }

  createTaller(data: any) {
    return this.http.post(`${this.baseUrl}/talleres`, data);
  }

  getUsuarios() {
    return this.http.get<Usuario[]>(`${this.baseUrl}/usuarios`);
  }

  updateUsuario(id: number, data: Partial<Usuario>) {
    return this.http.put<Usuario>(`${this.baseUrl}/usuarios/${id}`, data);
  }

  suspendUsuario(id: number) {
    return this.http.patch<Usuario>(`${this.baseUrl}/usuarios/${id}/suspender`, {});
  }

  deleteUsuario(id: number) {
    return this.http.delete(`${this.baseUrl}/usuarios/${id}`);
  }

  createUser(datos: any) {
    return this.http.post(`${environment.apiUrl}/auth/registro`, datos);
  }

  getBitacora() {
    return this.http.get<any[]>(`${this.baseUrl}/bitacora`);
  }
}

