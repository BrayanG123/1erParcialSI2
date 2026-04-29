import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ServicioService {
    private http = inject(HttpClient);
    private readonly API_URL = `${environment.apiUrl}/categorias`;

    getServicios() {
        return this.http.get<any[]>(`${this.API_URL}/`);
    }

    crearServicio(payload: any) {
        return this.http.post(`${this.API_URL}/`, payload);
    }

    eliminarServicio(id: number) {
        return this.http.delete(`${this.API_URL}/${id}`);
    }
}
