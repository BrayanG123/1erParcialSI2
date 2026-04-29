import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Evidencia {
  id: number;
  incidente_id: number;
  tipo: 'foto' | 'audio';
  url_archivo: string;
  procesado_ia: number;
  fecha_subida: string;
}

@Injectable({
  providedIn: 'root'
})
export class EvidenciaService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/evidencias`;

  getEvidenciasByIncidente(incidenteId: number): Observable<Evidencia[]> {
    return this.http.get<Evidencia[]>(`${this.baseUrl}/incidente/${incidenteId}`);
  }
}
