import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment.development';
import { Categoria_Item, Categoria_Create_Request } from '../models/categoria.model';

@Injectable({ providedIn: 'root' })
export class CategoriaService {
  private http = inject(HttpClient);
  private readonly API_URL = `${environment.apiUrl}/categorias`;

  getCategorias() {
    return this.http.get<Categoria_Item[]>(`${this.API_URL}/`);
  }

  crearCategoria(payload: Categoria_Create_Request) {
    return this.http.post<Categoria_Item>(`${this.API_URL}/`, payload);
  }

  actualizarCategoria(id: number, payload: Partial<Categoria_Create_Request>) {
    return this.http.patch<Categoria_Item>(`${this.API_URL}/${id}`, payload);
  }

  eliminarCategoria(id: number) {
    return this.http.delete(`${this.API_URL}/${id}`);
  }
}
