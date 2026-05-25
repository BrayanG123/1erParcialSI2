import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { forkJoin } from 'rxjs';

import { AdminOpsService } from '../../../../core/services/admin-ops.service';
import { IncidenteService } from '../../../../core/services/incidente.service';
import { environment } from '../../../../../environments/environment.development';

interface Request {
  descripcion: string;
  tiempo: string;
  prioridad: string;
}

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './admin-dashboard.component.html'
})
export class AdminDashboardComponent implements OnInit {

  private adminOpsService = inject(AdminOpsService);
  private incidenteService = inject(IncidenteService);


  // mapboxToken = environment.mapboxToken;

  loading = false;

  tallerName = 'Taller AutoFix';
  today = new Date();

  // KPIs
  stats = {
    nuevas: 0,
    enProceso: 0,
    completadasHoy: 0,
    tiempoPromedio: '18 min'
  };

  recentRequests: Request[] = [];

  // Dona
  solicitudesPorTipo = [
    { tipo: 'Batería', porcentaje: 30, color: '#3B82F6' },
    { tipo: 'Llanta', porcentaje: 20, color: '#F87171' },
    { tipo: 'Motor', porcentaje: 30, color: '#10B981' },
    { tipo: 'Choque', porcentaje: 10, color: '#FBBF24' },
    { tipo: 'Otros', porcentaje: 10, color: '#94A3B8' }
  ];

  ngOnInit(): void {
    this.cargarDashboard();
  }

  cargarDashboard(): void {
    this.loading = true;

    forkJoin({
      incidentes: this.incidenteService.getIncidentes(),
      disponibles: this.incidenteService.getIncidentesDisponibles(),
      servicios: this.adminOpsService.getServiciosRealizados(),
      asignaciones: this.adminOpsService.getAsignaciones()
    }).subscribe({
      next: (data) => {

        this.stats.nuevas = data.disponibles?.length ?? 0;

        this.stats.enProceso =
          data.asignaciones?.filter(a => a.estado !== 'Finalizado').length ?? 0;

        this.stats.completadasHoy = data.servicios?.length ?? 0;

        this.recentRequests = (data.incidentes ?? [])
          .slice(0, 4)
          .map((inc: any) => ({
            descripcion: inc.descripcion,
            tiempo: 'Hace 5 min',
            prioridad: this.getPrioridad(inc)
          }));

        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  private getPrioridad(inc: any): string {
    const desc = (inc.descripcion || '').toLowerCase();

    if (desc.includes('motor') || desc.includes('freno') || desc.includes('grave')) {
      return 'Alta';
    }

    if (desc.includes('llanta') || desc.includes('bateria')) {
      return 'Media';
    }

    return 'Baja';
  }
}
