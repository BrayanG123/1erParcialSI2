import { Component, Input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { DropdownComponent } from '../../ui/dropdown/dropdown.component';
import { DropdownItemTwoComponent } from '../../ui/dropdown/dropdown-item/dropdown-item.component-two';

@Component({
  selector: 'app-user-dropdown',
  standalone: true,
  imports: [CommonModule, RouterModule, DropdownComponent, DropdownItemTwoComponent],
  templateUrl: './user-dropdown.component.html'
})
export class UserDropdownComponent {
  private router = inject(Router);

  @Input() userName: string = 'Usuario';
  @Input() userRole: string = 'Administrador';

  isOpen = false;

  toggleDropdown() {
    this.isOpen = !this.isOpen;
  }

  closeDropdown() {
    this.isOpen = false;
  }

  logout() {
    localStorage.removeItem('token'); // O localStorage.clear() si prefieres borrar todo
    this.router.navigate(['/login']);
  }
}
