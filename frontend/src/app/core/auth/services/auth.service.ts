import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap, switchMap, of, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { AuthResponse, LoginCredentials } from '../models/auth.model';
import { RolUsuario } from '../../../features/usuarios/models/usuario.model';
import { RoleService } from './role.service';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);
  private roleService = inject(RoleService);
  private tokenEnMemoria: string | null = null;

  private readonly AUTH_URL = `${environment.apiUrl}/auth`;

  private saveToStorage(key: string, value: string): void {
    if (key === 'access_token') this.tokenEnMemoria = value;
    try {
      localStorage.setItem(key, value);
    } catch {
      try { sessionStorage.setItem(key, value); } catch { }
    }
  }

  private getFromStorage(key: string): string | null {
    if (key === 'access_token' && this.tokenEnMemoria) return this.tokenEnMemoria;
    return localStorage.getItem(key) ?? sessionStorage.getItem(key);
  }

  private removeFromStorage(key: string): void {
    if (key === 'access_token') this.tokenEnMemoria = null;
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  }

  login(credentials: LoginCredentials) {
    const email = credentials.email.trim();
    const body = new HttpParams()
      .set('username', email)
      .set('password', credentials.password || '');

    return this.http.post<AuthResponse>(`${this.AUTH_URL}/login`, body.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).pipe(
      switchMap(res => {
        this.saveToStorage('access_token', res.access_token);
        const payload = this.decodeToken(res.access_token);
        const rawRole = payload.rol ?? payload.role ?? '';

        this.roleService.setRole(rawRole);
        this.saveToStorage('role', rawRole); // ✅ FIX 1: persistir rol en storage

        if (rawRole === 'administrador') {
          return this.getProfile().pipe(
            tap(profile => {
              const hasTaller = !!profile.perfil_administrador?.taller;
              this.saveToStorage('has_taller', hasTaller ? 'true' : 'false');
              if (hasTaller) {
                this.router.navigate(['/admin/dashboard']);
              } else {
                this.router.navigate(['/setup-taller']);
              }
            })
          );
        } else {
          this.redirectByRole(rawRole);
          return of(res);
        }
      })
    );
  }

  getProfile(): Observable<any> {
    return this.http.get<any>(`${environment.apiUrl}/usuarios/me`);
  }

  private decodeToken(token: string): any {
    try {
      const base64Url = token.split('.')[1] || '';
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const padded = base64.padEnd(base64.length + (4 - (base64.length % 4)) % 4, '=');
      return JSON.parse(window.atob(padded));
    } catch {
      return {};
    }
  }

  private redirectByRole(rol: string): void {
    if (rol === 'superadmin') {
      this.router.navigate(['/superadmin/dashboard']);
    } else if (rol === 'administrador') {
      this.router.navigate(['/admin/dashboard']);
    } else if (rol === 'cliente') {
      this.router.navigate(['/cliente/perfil']);
    } else {
      this.router.navigate(['/login']);
    }
  }

  getToken(): string | null {
    return this.getFromStorage('access_token');
  }

  logout(): void {
    this.removeFromStorage('access_token');
    this.removeFromStorage('has_taller');
    this.removeFromStorage('role');
    this.roleService.clearRole();
    this.router.navigate(['/login']);
  }

  getRole(): RolUsuario | null {
    const role = this.getFromStorage('role');
    return role ? (role as RolUsuario) : null;
  }
}
