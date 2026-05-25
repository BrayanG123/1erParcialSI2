import { Component } from '@angular/core';
import { CommonModule } from '@angular/common'; // Agregamos CommonModule para el dropdown
import { DropdownComponent } from '../ui/dropdown/dropdown.component';
import { DropdownItemComponent } from '../ui/dropdown/dropdown-item/dropdown-item.component';

@Component({
  selector: 'app-monthly-target',
  standalone: true,
  imports: [
    CommonModule, 
    DropdownComponent, 
    DropdownItemComponent
  ],
  templateUrl: './monthly-target.component.html',
})
export class MonthlyTargetComponent {
  // Mantenemos estas variables por si quieres mostrar el texto del porcentaje
  public progressValue: number = 75.55;
  
  isOpen = false;

  toggleDropdown() {
    this.isOpen = !this.isOpen;
  }

  closeDropdown() {
    this.isOpen = false;
  }
}
