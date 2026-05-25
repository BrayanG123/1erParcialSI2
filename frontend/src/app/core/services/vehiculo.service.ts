import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment.development';
import { Vehiculo, VehiculoCreate } from '../models/vehiculo.model';

@Injectable({
  providedIn: 'root'
})
export class VehiculoService {
  private http = inject(HttpClient);
  private readonly URL = `${environment.apiUrl}/vehiculos`;

  getMisVehiculos(): Observable<Vehiculo[]> {
    return this.http.get<Vehiculo[]>(`${this.URL}/mis-vehiculos`);
  }

  getAllVehiculos(): Observable<Vehiculo[]> {
    return this.http.get<Vehiculo[]>(this.URL);
  }

  getVehiculoById(id: number): Observable<Vehiculo> {
    return this.http.get<Vehiculo>(`${this.URL}/${id}`);
  }

  registrarVehiculo(vehiculo: VehiculoCreate): Observable<Vehiculo> {
    return this.http.post<Vehiculo>(this.URL, vehiculo);
  }

  actualizarVehiculo(id: number, vehiculo: Partial<VehiculoCreate>): Observable<Vehiculo> {
    return this.http.patch<Vehiculo>(`${this.URL}/${id}`, vehiculo);
  }

  eliminarVehiculo(id: number): Observable<void> {
    return this.http.delete<void>(`${this.URL}/${id}`);
  }
}
