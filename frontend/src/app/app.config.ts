import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { routes } from './app.routes';
import { authInterceptor } from './core/auth/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    // Optimización de detección de cambios (estándar en Angular 18/19)
    provideZoneChangeDetection({ eventCoalescing: true }), 
    
    // Configuración de las rutas que definimos antes
    provideRouter(routes), 
    
    // Configuración del cliente HTTP con tu interceptor de seguridad
    provideHttpClient(
      withInterceptors([authInterceptor])
    )
  ]
};
