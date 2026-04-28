import { CommonModule } from '@angular/common';
import { Component, computed, signal } from '@angular/core';

@Component({
  selector: 'app-cliente-perfil',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './cliente-perfil.component.html',
})
export class ClientePerfilComponent {
  token = signal<string>(localStorage.getItem('token') || '');

  decoded = computed(() => {
    const t = this.token();
    if (!t || t.split('.').length < 2) return null;
    try {
      return JSON.parse(atob(t.split('.')[1]));
    } catch {
      return null;
    }
  });

  copyToken() {
    const t = this.token();
    if (!t) return;
    navigator.clipboard?.writeText(t);
  }
}

