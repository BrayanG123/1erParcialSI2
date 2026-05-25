import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
//import { ChartTabComponent } from '../common/chart-tab/chart-tab.component';

@Component({
  selector: 'app-statics-chart',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './statics-chart.component.html',
})
export class StaticsChartComponent {

  // Datos simulados para las barras de servicios
  public salesData = [120, 250, 180, 320, 210, 240, 390, 150, 280, 310, 260, 340];
}
