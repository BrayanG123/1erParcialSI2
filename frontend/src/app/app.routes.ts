import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/pages/login/login.component';
import { RegisterComponent } from './features/auth/pages/register/register.component';
import { authGuard } from './core/auth/guards/auth.guard';

export const routes: Routes = [
  // 1. RUTA RAÍZ: Redirige al login de entrada (Sin guards para evitar pantalla blanca)
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'login'
  },

  // 2. RUTAS PÚBLICAS: Cualquiera puede entrar
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  {
    path: 'setup-taller',
    canActivate: [authGuard],           // ← solo authGuard, él ya maneja el resto
    data: { expectedRole: 'administrador' },
    loadComponent: () => import('./features/admin/pages/setup-taller/setup-taller.component')
      .then(m => m.SetupTallerComponent)
  },
  // 👑 SECCIÓN SUPERADMIN (admin@vehiassist.com)
  {
    path: 'superadmin',
    canActivate: [authGuard],
    data: { expectedRole: 'superadmin' },
    loadComponent: () => import('./shared/layouts/admin-layout/admin-layout.component').then(m => m.AdminLayoutComponent),
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () => import('./features/dashboard/pages/superadmin/dashboard.component').then(m => m.DashboardComponent)
      },
      {
        path: 'talleres',
        loadComponent: () => import('./features/talleres/pages/talleres-gestion.component').then(m => m.TalleresGestionComponent)
      },
      {
        path: 'usuarios',
        loadComponent: () => import('./features/usuarios/pages/usuarios-gestion.component').then(m => m.UsuariosGestionComponent)
      },
      {
        path: 'perfil',
        loadComponent: () => import('./features/superadmin/pages/perfil/perfil.component').then(m => m.SuperadminPerfilComponent)
      },
      {
        path: 'vehiculos',
        loadComponent: () => import('./features/superadmin/pages/vehiculos-gestion/vehiculos-gestion.component').then(m => m.VehiculosGestionComponent)
      },
      {
        path: 'bitacora',
        loadComponent: () => import('./features/superadmin/pages/bitacora/bitacora.component').then(m => m.BitacoraComponent)
      },
      {
        path: 'categorias',
        loadComponent: () => import('./features/categorias/pages/categorias.component').then(m => m.CategoriasComponent)
      }
    ]
  },

  // 🛠️ SECCIÓN ADMIN TALLER (juan2020@gmail.com)
  {
    path: 'admin',
    canActivate: [authGuard],
    data: { expectedRole: 'administrador' },
    loadComponent: () => import('./shared/layouts/admin-layout/admin-layout.component').then(m => m.AdminLayoutComponent),
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () => import('./features/dashboard/pages/admin/admin-dashboard.component').then(m => m.AdminDashboardComponent)
      },
      {
        path: 'usuarios',
        loadComponent: () => import('./features/admin/pages/gestion-mecanicos/mecanicos-list.component').then(m => m.MecanicosListComponent)
      },
      {
        path: 'mecanicos',
        loadComponent: () => import('./features/admin/pages/gestion-mecanicos/mecanicos-list.component').then(m => m.MecanicosListComponent)
      },
      {
        path: 'servicios',
        loadComponent: () => import('./features/admin/pages/gestion-servicios/servicios-list.component').then(m => m.ServiciosListComponent)
      },
      {
        path: 'servicios-realizados',
        loadComponent: () => import('./features/admin/pages/servicios-realizados/servicios-realizados.component').then(m => m.ServiciosRealizadosComponent)
      },
      {
        path: 'asignaciones',
        loadComponent: () => import('./features/admin/pages/asignaciones/asignaciones.component').then(m => m.AsignacionesComponent)
      },
      {
        path: 'pagos',
        loadComponent: () => import('./features/admin/pages/Pagos/pagos.component').then(m => m.PagosComponent)
      },
      {
        path: 'reportes',
        loadComponent: () => import('./features/admin/pages/reportes/reportes.component').then(m => m.ReportesComponent)
      },
      {
        path: 'comisiones',
        loadComponent: () => import('./features/admin/pages/comisiones/comisiones.component').then(m => m.ComisionesComponent)
      },
      {
        path: 'categorias',
        loadComponent: () => import('./features/categorias/pages/categorias.component').then(m => m.CategoriasComponent)
      },
      {
        path: 'bitacora',
        loadComponent: () => import('./features/admin/pages/bitacora/bitacora.component').then(m => m.BitacoraComponent)
      },
      {
        path: 'incidentes',
        loadComponent: () => import('./features/admin/pages/incidentes/incidentes-list.component').then(m => m.IncidentesListComponent)
      },
      {
        path: 'incidentes/:id/evidencias',
        loadComponent: () => import('./features/admin/pages/evidencias/evidencias.component').then(m => m.EvidenciasComponent)
      },
      {
        path: 'disponibilidad',
        loadComponent: () => import('./features/admin/pages/disponibilidad/disponibilidad.component').then(m => m.DisponibilidadComponent)
      },
      {
        path: 'seguimiento',
        loadComponent: () => import('./features/admin/pages/seguimiento/seguimiento.component').then(m => m.SeguimientoComponent)
      }
    ]
  },
  // 👤 SECCIÓN CLIENTE (solo perfil + JWT)
  {
    path: 'cliente',
    canActivate: [authGuard],
    data: { expectedRole: 'cliente' },
    loadComponent: () => import('./shared/layouts/cliente-layout/cliente-layout.component').then(m => m.ClienteLayoutComponent),
    children: [
      { path: '', redirectTo: 'perfil', pathMatch: 'full' },
      {
        path: 'perfil',
        loadComponent: () => import('./features/cliente/pages/perfil/cliente-perfil.component').then(m => m.ClientePerfilComponent)
      }
    ]
  },

  // 3. COMODÍN: Si escriben cualquier cosa mal, al login
  { path: '**', redirectTo: 'login' }
];
