import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { Usuario } from '../../features/usuarios/models/usuario.model';

@Injectable({ providedIn: 'root' })
export class MecanicoService {
  private http = inject(HttpClient);
  private readonly API_URL = `${environment.apiUrl}`;

  // Listar: Filtramos en el frontend para asegurar que solo vemos mecánicos
  getMecanicos() {
  return this.http.get<any[]>(`${this.API_URL}/admin/usuarios`).pipe(
    map(usuarios => usuarios
      .filter(u => u.rol === 'mecanico')
      .map(u => ({
        id: u.perfil_mecanico_id ?? u.id, // ← necesitas que el backend devuelva esto
        nombre: u.nombre,
        apellido: u.apellido
      }))
    )
  );
}

  // Crear: Mandamos el payload exacto que pide /auth/registro
  crearMecanico(payload: any) {
    return this.http.post(`${this.API_URL}/auth/registro`, payload);
  }

  // Eliminar: Endpoint de administración
  eliminarMecanico(id: number) {
    return this.http.delete(`${this.API_URL}/admin/usuarios/${id}`);
  }
}
