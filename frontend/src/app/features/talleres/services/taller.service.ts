import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment.development';
import { Observable } from 'rxjs';
import { Taller } from '../models/taller.model';

@Injectable({ providedIn: 'root' })
export class TallerService {
  private http = inject(HttpClient);
   private readonly URL = `${environment.apiUrl}/auth/setup-taller`;

  registrarTaller(datosTaller: any): Observable<Taller> {
    return this.http.post<Taller>(this.URL, datosTaller);
  }

  getMiTaller(): Observable<Taller> {
    return this.http.get<Taller>(`${this.URL}/mi-taller`); // ← necesario para los guards
  }
}
