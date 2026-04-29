import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IncidenteService } from '../../../../core/services/incidente.service';
import { MecanicoService } from '../../../../core/services/mecanico.service';
import { AsignacionService } from '../../../../core/services/asignacion.service';
import { AsignacionRequest } from '../../../../core/models/asignacion.model';

@Component({
  selector: 'app-asignaciones',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './asignaciones.component.html'
})
export class AsignacionesComponent implements OnInit {
  private incidenteService = inject(IncidenteService);
  private mecanicoService = inject(MecanicoService);
  private asignacionService = inject(AsignacionService);

  // Datos
  incidentesPendientes: any[] = [];
  asignacionesActivas: any[] = [];
  mecanicos: any[] = [];
  
  // UI State
  loading = false;
  view: 'list' | 'detail' = 'list';
  selectedAsignacion: any | null = null;
  nuevoEstado: string = '';
  
  // Stepper config
  pasos = ['Aceptado', 'En camino', 'En proceso', 'Finalizado'];

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.loading = true;
    
    // Incidentes sin asignar
    this.incidenteService.getIncidentesDisponibles().subscribe({
      next: (data) => this.incidentesPendientes = Array.isArray(data) ? data : [],
      error: () => this.incidentesPendientes = []
    });

    // Asignaciones actuales
    this.asignacionService.getAsignaciones().subscribe({
      next: (data) => {
        this.asignacionesActivas = Array.isArray(data) ? data : [];
        this.loading = false;
      },
      error: () => {
        this.asignacionesActivas = [];
        this.loading = false;
      }
    });

    // Técnicos
    this.mecanicoService.getMecanicos().subscribe({
      next: (data) => this.mecanicos = Array.isArray(data) ? data : [],
      error: () => this.mecanicos = []
    });
  }

  seleccionarAsignacion(asig: any): void {
    this.selectedAsignacion = asig;
    this.nuevoEstado = asig.estado;
    this.view = 'detail';
  }

  asignarMecanico(incidente: any, mecanicoId: string): void {
    if (!mecanicoId) return;

    const payload: AsignacionRequest = {
      incidente_id: incidente.id,
      mecanico_id: parseInt(mecanicoId),
      notas: 'Asignación desde el panel de operaciones'
    };

    this.loading = true;
    this.asignacionService.crearAsignacion(payload).subscribe({
      next: (res) => {
        // Al asignar, pasamos directamente al detalle del seguimiento
        this.cargarDatos();
        this.view = 'list'; // O podríamos buscar la nueva asignación y mostrarla
        alert('Técnico asignado con éxito');
      },
      error: () => {
        this.loading = false;
        alert('Error al realizar la asignación');
      }
    });
  }

  actualizarEstado(): void {
    if (!this.selectedAsignacion || !this.nuevoEstado) return;
    
    this.asignacionService.actualizarEstado(this.selectedAsignacion.id, this.nuevoEstado).subscribe({
      next: () => {
        this.selectedAsignacion.estado = this.nuevoEstado;
        alert('Estado actualizado');
      },
      error: () => alert('Error al actualizar el estado')
    });
  }

  getStepStatus(paso: string): 'completed' | 'current' | 'pending' {
    const currentIndex = this.pasos.indexOf(this.selectedAsignacion.estado);
    const stepIndex = this.pasos.indexOf(paso);
    
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'current';
    return 'pending';
  }

  volver(): void {
    this.view = 'list';
    this.selectedAsignacion = null;
  }
}
