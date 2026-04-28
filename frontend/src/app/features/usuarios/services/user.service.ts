import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import { Usuario } from '../models/usuario.model';

@Injectable({ providedIn: 'root' })
export class UserService {
  private http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/usuarios`;

  getMe() {
    return this.http.get<Usuario>(`${this.baseUrl}/me`);
  }

  updateMe(data: any) {
    return this.http.patch<Usuario>(`${this.baseUrl}/me`, data);
  }
}
