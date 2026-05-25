import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { RoleService } from '../services/role.service';

export const authGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  const roleService = inject(RoleService);

  const token =
    localStorage.getItem('access_token') ||
    sessionStorage.getItem('access_token');

  if (!token) {
    router.navigate(['/login']);
    return false;
  }

  const expectedRole = route.data['expectedRole'];
  if (expectedRole) {
    const currentRole = roleService.getRole();
    console.log('🛡️ Rol esperado:', expectedRole, '| Rol actual:', currentRole);

    if (currentRole !== expectedRole) {
      switch (currentRole) {
        case 'superadmin': router.navigate(['/superadmin/dashboard']); break;
        case 'administrador': {
          const hasTaller = localStorage.getItem('has_taller') === 'true';
          router.navigate([hasTaller ? '/admin/dashboard' : '/setup-taller']);
          break;
        }
        default: router.navigate(['/login']);
      }
      return false;
    }

    // Si es admin y está en una ruta que NO es setup-taller, verificar si tiene taller
    if (currentRole === 'administrador' && !state.url.includes('/setup-taller')) {
      const hasTaller = localStorage.getItem('has_taller') === 'true';
      if (!hasTaller) {
        router.navigate(['/setup-taller']);
        return false;
      }
    }
    
    // Si ya tiene taller y trata de entrar a setup-taller, mandarlo al dashboard
    if (currentRole === 'administrador' && state.url.includes('/setup-taller')) {
      const hasTaller = localStorage.getItem('has_taller') === 'true';
      if (hasTaller) {
        router.navigate(['/admin/dashboard']);
        return false;
      }
    }
  }

  return true;
};
