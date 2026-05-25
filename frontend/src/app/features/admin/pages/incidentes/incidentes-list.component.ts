import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IncidenteService } from '../../../../core/services/incidente.service';
import { MecanicoService } from '../../../../core/services/mecanico.service';
import { AsignacionService } from '../../../../core/services/asignacion.service';
import { AsignacionRequest } from '../../../../core/models/asignacion.model';

@Component({
  selector: 'app-incidentes-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './incidentes-list.component.html'
})
export class IncidentesListComponent implements OnInit {
  private incidenteService = inject(IncidenteService);
  private mecanicoService = inject(MecanicoService);
  private asignacionService = inject(AsignacionService);

  // Pestañas
  tabActiva: 'pendientes' | 'historial' = 'pendientes';

  // Datos
  incidentesPendientes: any[] = [];
  incidentesHistorial: any[] = [];
  mecanicos: any[] = [];

  // UI
  loading = false;
  notificacion: string | null = null;
  error: string | null = null;

  // Filtros
  filtroPrioridad = '';
  filtroDistancia = '50';
  searchTerm = '';

  ngOnInit(): void {
    this.cargarDatos();
  }

  cambiarTab(tab: 'pendientes' | 'historial') {
    this.tabActiva = tab;
  }

  cargarDatos() {
    this.loading = true;

    // Incidentes disponibles (sin asignar)
    this.incidenteService.getIncidentesDisponibles().subscribe({
      next: (data) => {
        this.incidentesPendientes = Array.isArray(data) ? data.map(inc => ({
          ...inc,
          distancia: (Math.random() * 10 + 1).toFixed(1) + ' km', // Dato estático como pidió el usuario
          tiempo: `Hace ${Math.floor(Math.random() * 30 + 5)} min`, // Dato estático
          prioridad: this.determinarPrioridad(inc)
        })) : [];
        this.loading = false;
      },
      error: () => {
        this.incidentesPendientes = [];
        this.loading = false;
      }
    });

    // Historial — incidentes ya asignados al taller
    this.incidenteService.getIncidentes().subscribe({
      next: (data) => {
        this.incidentesHistorial = Array.isArray(data) ? data : [];
      },
      error: () => {
        this.incidentesHistorial = [];
      }
    });

    // Mecánicos del taller
    this.mecanicoService.getMecanicos().subscribe({
      next: (data) => this.mecanicos = Array.isArray(data) ? data : [],
      error: () => this.mecanicos = []
    });
  }

  asignarMecanico(incidenteId: number, event: any) {
    const mecanicoId = event?.target?.value;
    if (!mecanicoId) return;

    const datos: AsignacionRequest = {
      incidente_id: incidenteId,
      mecanico_id: parseInt(mecanicoId),
      notas: 'Asignación desde panel administrador'
    };

    this.asignacionService.crearAsignacion(datos).subscribe({
      next: () => {
        // Quitar de pendientes y recargar historial
        this.incidentesPendientes = this.incidentesPendientes.filter(i => i.id !== incidenteId);
        this.incidenteService.getIncidentes().subscribe({
          next: (data) => this.incidentesHistorial = Array.isArray(data) ? data : []
        });
        this.mostrarNotificacion('Mecánico asignado con éxito');
      },
      error: (err) => {
        this.mostrarError(err?.error?.detail || 'No se pudo completar la asignación');
      }
    });
  }

  private determinarPrioridad(inc: any): 'Alta' | 'Media' | 'Baja' {
    const desc = (inc.descripcion || '').toLowerCase();
    const cat = (inc.categoria?.nombre || '').toLowerCase();
    
    if (desc.includes('choque') || desc.includes('accidente') || desc.includes('fuego') || cat.includes('emergencia')) {
      return 'Alta';
    }
    if (desc.includes('motor') || desc.includes('frenos') || desc.includes('arranca')) {
      return 'Media';
    }
    return 'Baja';
  }

  getPrioridadBadgeClass(prioridad: string): string {
    switch (prioridad) {
      case 'Alta': return 'bg-red-50 text-red-600';
      case 'Media': return 'bg-orange-50 text-orange-600';
      case 'Baja': return 'bg-emerald-50 text-emerald-600';
      default: return 'bg-gray-50 text-gray-600';
    }
  }

  getFilteredIncidentes() {
    return this.incidentesPendientes.filter(inc => {
      const matchSearch = !this.searchTerm || 
        inc.descripcion.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        inc.id.toString().includes(this.searchTerm);
      
      const matchPrioridad = !this.filtroPrioridad || inc.prioridad === this.filtroPrioridad;
      
      const distanciaNum = parseFloat(inc.distancia);
      const matchDistancia = this.filtroDistancia === '50' || distanciaNum <= parseInt(this.filtroDistancia);
      
      return matchSearch && matchPrioridad && matchDistancia;
    });
  }

  rechazarIncidente(id: number) {
    if (confirm('¿Estás seguro de rechazar esta solicitud?')) {
      this.incidentesPendientes = this.incidentesPendientes.filter(i => i.id !== id);
      this.mostrarNotificacion('Solicitud rechazada');
    }
  }

  verDetalle(inc: any) {
    // Por ahora solo mostrar un alert o log, ya que no hay ruta de detalle especificada
    alert(`Detalle del Incidente #${inc.id}\nDescripción: ${inc.descripcion}\nUbicación: ${inc.latitud}, ${inc.longitud}`);
  }

  private mostrarNotificacion(msg: string) {
    this.notificacion = msg;
    this.error = null;
    setTimeout(() => this.notificacion = null, 3000);
  }

  private mostrarError(msg: string) {
    this.error = msg;
    this.notificacion = null;
    setTimeout(() => this.error = null, 4000);
  }
}
