import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IncidenteService } from '../../../../core/services/incidente.service';
import { MecanicoService } from '../../../../core/services/mecanico.service';
import { AsignacionService } from '../../../../core/services/asignacion.service';
import { AsignacionRequest } from '../../../../core/models/asignacion.model';

@Component({
  selector: 'app-incidentes-list',
  standalone: true,
  imports: [CommonModule],
    templateUrl: '../incidentes/incidentes-list.component.html'
})
export class IncidentesListComponent implements OnInit {
  private incidenteService = inject(IncidenteService);
  private mecanicoService = inject(MecanicoService);
  private asignacionService = inject(AsignacionService);

  incidentes: any[] = [];
  mecanicos: any[] = [];
  loading = false;
  notificacion: string | null = null;
  error: string | null = null;

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos() {
    this.loading = true;
    this.incidenteService.getIncidentesDisponibles().subscribe({
      next: (data) => {
        this.incidentes = Array.isArray(data) ? data : [];
        this.loading = false;
      },
      error: () => {
        this.incidentes = [];
        this.loading = false;
      }
    });

    this.mecanicoService.getMecanicos().subscribe({
      next: (data) => (this.mecanicos = Array.isArray(data) ? data : []),
      error: () => (this.mecanicos = [])
    });
  }

  asignarMecanico(incidenteId: number, event: any) { // ✅ método agregado
    const mecanicoId = event?.target?.value;
    if (!mecanicoId) return;

    const datos: AsignacionRequest = {
      incidente_id: incidenteId,
      mecanico_id: parseInt(mecanicoId),
      notas: 'Asignación automática desde panel administrador'
    };

    this.asignacionService.crearAsignacion(datos).subscribe({
      next: () => {
        this.incidentes = this.incidentes.filter(i => i.id !== incidenteId);
        this.mostrarNotificacion('✅ Mecánico asignado con éxito');
      },
      error: (err) => {
        console.error('Error al asignar:', err);
        this.mostrarError('❌ No se pudo completar la asignación');
      }
    });
  }

  private mostrarNotificacion(msg: string) {
    this.notificacion = msg;
    this.error = null;
    setTimeout(() => this.notificacion = null, 3000);
  }

  private mostrarError(msg: string) {
    this.error = msg;
    this.notificacion = null;
    setTimeout(() => this.error = null, 3000);
  }
}
