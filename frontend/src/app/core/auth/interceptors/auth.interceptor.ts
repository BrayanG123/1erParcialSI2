import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { environment } from '../../../../environments/environment';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = (authService.getToken() ?? '').trim();

  const isApiUrl = req.url.startsWith(environment.apiUrl);

  console.log('🔑 Token existe:', !!token);
  console.log('🌐 URL:', req.url);
  console.log('✅ isApiUrl:', isApiUrl);

  if (token && isApiUrl) {
    const cloned = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
    return next(cloned);
  }

  return next(req);
};
