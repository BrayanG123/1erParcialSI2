import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-bar-chart-one',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './bar-chart-one.component.html',
  styles: ``
})
export class BarChartOneComponent {
  // Solo dejamos los datos, sin importar librerías que rompan la compilación
  public salesData = [168, 385, 201, 298, 187, 195, 291, 110, 215, 390, 280, 112];
}
