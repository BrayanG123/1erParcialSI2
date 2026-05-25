import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-superadmin-layout',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule],
  templateUrl: './superadmin-layout.component.html',
  styleUrl: './superadmin-layout.component.css'
})
export class SuperadminLayoutComponent {
  // Lista de navegación para el Superadmin
  menuItems = [
    { label: 'Panel Global', icon: 'dashboard', route: '/superadmin/dashboard' },
    { label: 'Talleres', icon: 'storefront', route: '/superadmin/talleres' },
    { label: 'Usuarios', icon: 'people', route: '/superadmin/usuarios' },
    { label: 'Globales', icon: 'sell', route: '/superadmin/categorias' }, // ¡Aquí está el acceso!
    { label: 'Vehículos', icon: 'directions_car', route: '/superadmin/vehiculos' },
    { label: 'Bitácora', icon: 'history', route: '/superadmin/bitacora' }
  ];
}