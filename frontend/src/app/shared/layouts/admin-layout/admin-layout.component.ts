import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router } from '@angular/router';
import { SidebarService } from '../../services/sidebar.service';
import { AppHeaderComponent } from './components/header/app-header/app-header.component';
import { AppSidebarComponent } from './components/sidebar/app-sidebar/app-sidebar.component';
import { AuthService } from '../../../core/auth/services/auth.service';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [
    CommonModule, 
    RouterOutlet, 
    AppSidebarComponent, // El nombre que le diste al componente
    AppHeaderComponent   // El nombre que le diste al componente
  ],
  templateUrl: './admin-layout.component.html',
  styles: [`
    :host { display: block; height: 100vh; }
  `]
})
export class AdminLayoutComponent implements OnInit {
  private router = inject(Router);
  private authService = inject(AuthService);
  // Inyectamos el servicio público para que el HTML pueda usarlo
  public sidebarService = inject(SidebarService);

  ngOnInit() {
    const token = this.authService.getToken(); 
    if (!token) {
      this.logout();
      return;
    }
    // Tu lógica de carga de token está perfecta aquí
  }

  logout() {
    this.authService.logout();
  }
}
