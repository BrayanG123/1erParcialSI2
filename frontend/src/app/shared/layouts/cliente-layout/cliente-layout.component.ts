import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { Router, RouterModule, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-cliente-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterModule],
  templateUrl: './cliente-layout.component.html',
})
export class ClienteLayoutComponent {
  private router = inject(Router);

  logout() {
    localStorage.clear();
    this.router.navigate(['/login']);
  }
}

