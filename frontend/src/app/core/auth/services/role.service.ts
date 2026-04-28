import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class RoleService {
  private rolEnMemoria: string = ''; 
  private normalizeRole(role: string | null | undefined): string {
    const normalized = (role || '').toLowerCase().trim();
    if (normalized === 'admin') {
      return 'administrador';
    }
    return normalized;
  }

  // Guarda el rol en el LocalStorage al loguearse
   setRole(role: string): void {
    const normalized = this.normalizeRole(role);
    this.rolEnMemoria = normalized; // ✅ siempre en memoria
    try {
      localStorage.setItem('role', normalized);
    } catch {
      try { sessionStorage.setItem('role', normalized); } catch {}
    }
  }

  // Obtiene el rol actual
  getRole(): string {
    if (this.rolEnMemoria) return this.rolEnMemoria; // ✅ primero memoria
    return this.normalizeRole(
      localStorage.getItem('role') ?? sessionStorage.getItem('role')
    );
  }

  // Verifica si es Superadmin
  isSuperAdmin(): boolean {
    return this.getRole() === 'superadmin';
  }

  // Verifica si es Admin de Taller (dueño)
  isAdmin(): boolean {
    return this.getRole() === 'administrador';
  }

  // Verifica si es Cliente (el que usa la app móvil pero entra a la web por el token)
  isCliente(): boolean {
    return this.getRole() === 'cliente';
  }

  // Limpia el rol (útil para el logout)
  clearRole(): void {
  this.rolEnMemoria = '';          // ✅ limpiar memoria
  localStorage.removeItem('role');
  sessionStorage.removeItem('role'); // ✅ limpiar sessionStorage también
 }
}
