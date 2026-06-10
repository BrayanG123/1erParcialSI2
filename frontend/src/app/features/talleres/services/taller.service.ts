import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment.development';
import { Observable } from 'rxjs';
import { Taller } from '../models/taller.model';

/**
 * Respuesta del endpoint POST /auth/setup-taller.
 * Además del taller creado, el backend devuelve un JWT nuevo que ya
 * incluye el tenant_id recién generado.
 */
export interface SetupTallerResponse {
  message: string;
  taller_id: number;
  access_token: string;
  refresh_token?: string;
  token_type: string;
}

@Injectable({ providedIn: 'root' })
export class TallerService {
  private http = inject(HttpClient);
   private readonly URL = `${environment.apiUrl}/auth/setup-taller`;

  registrarTaller(datosTaller: any): Observable<SetupTallerResponse> {
    return this.http.post<SetupTallerResponse>(this.URL, datosTaller);
  }

  getMiTaller(): Observable<Taller> {
    return this.http.get<Taller>(`${this.URL}/mi-taller`); // ← necesario para los guards
  }
}
