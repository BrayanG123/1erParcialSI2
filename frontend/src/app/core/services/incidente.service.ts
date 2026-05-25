import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment.development';
import { Incidente } from '../models/incidente.model';

@Injectable({ providedIn: 'root' })
export class IncidenteService {
    private http = inject(HttpClient);
    private readonly API_URL = `${environment.apiUrl}/incidentes`;

     // ADMIN: incidentes disponibles para asignar
    getIncidentesDisponibles() {
        return this.http.get<Incidente[]>(`${this.API_URL}/disponibles`);
    }

    // ADMIN: historial de incidentes del taller
    getIncidentes() {
        return this.http.get<Incidente[]>(`${this.API_URL}/`);
    }

    getIncidenteById(id: number) {
        return this.http.get<Incidente>(`${this.API_URL}/${id}`);
    }

    actualizarIncidente(id: number, datos: Partial<Incidente>) {
        return this.http.patch<Incidente>(`${this.API_URL}/${id}`, datos);
    }
}
