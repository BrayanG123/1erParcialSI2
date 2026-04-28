import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-monthly-sales-chart',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './monthly-sales-chart.component.html',
})
export class MonthlySalesChartComponent {
  // Dejamos los datos por si quieres mostrarlos en texto después
  public series = [
    {
      name: 'Ventas',
      data: [44, 55, 57, 56, 61, 58, 63, 60, 66]
    }
  ];
}
