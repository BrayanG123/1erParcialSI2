import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AsignacionService } from '../../../../core/services/asignacion.service';
import { MecanicoService } from '../../../../core/services/mecanico.service';

@Component({
  selector: 'app-asignaciones',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './asignaciones.component.html'
})
export class AsignacionesComponent implements OnInit {
  private asignacionService = inject(AsignacionService);
  private mecanicoService = inject(MecanicoService);

  asignacionesActivas: any[] = [];
  mecanicos: any[] = [];

  loading = false;
  asignando: number | null = null;   // id de la asignación que se está procesando
  notificacion: string | null = null;
  error: string | null = null;
  ordenRecientes = true;

  // Paginación (cliente)
  pagina = 1;
  tamanoPagina = 10;
  Math = Math; // para usar Math.min en el template

  view: 'list' | 'detail' = 'list';
  selectedAsignacion: any | null = null;
  nuevoEstado = '';

  pasos = ['Aceptado', 'En camino', 'En proceso', 'Finalizado'];

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.loading = true;
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

    this.mecanicoService.getMecanicos().subscribe({
      next: (data) => (this.mecanicos = Array.isArray(data) ? data : []),
      error: () => (this.mecanicos = [])
    });
  }

  getAsignacionesOrdenadas(): any[] {
    const factor = this.ordenRecientes ? -1 : 1;
    return [...this.asignacionesActivas].sort(
      (a, b) => factor * (new Date(a.fecha_creacion).getTime() - new Date(b.fecha_creacion).getTime())
    );
  }

  toggleOrden(): void {
    this.ordenRecientes = !this.ordenRecientes;
    this.pagina = 1;
  }

  // ── Paginación ──────────────────────────────────────────────

  getAsignacionesPagina(): any[] {
    const inicio = (this.pagina - 1) * this.tamanoPagina;
    return this.getAsignacionesOrdenadas().slice(inicio, inicio + this.tamanoPagina);
  }

  get totalPaginas(): number {
    return Math.max(1, Math.ceil(this.asignacionesActivas.length / this.tamanoPagina));
  }

  cambiarPagina(delta: number): void {
    const nueva = this.pagina + delta;
    if (nueva < 1 || nueva > this.totalPaginas) return;
    this.pagina = nueva;
  }

  resetPagina(): void {
    this.pagina = 1;
  }

  asignarMecanico(asig: any, mecanicoId: string, event?: Event): void {
    event?.stopPropagation();
    if (!mecanicoId) return;

    this.asignando = asig.id;
    this.asignacionService.asignarMecanico(asig.id, parseInt(mecanicoId, 10)).subscribe({
      next: (actualizada: any) => {
        // Reemplazar la asignación en la lista con la versión actualizada del backend
        this.asignacionesActivas = this.asignacionesActivas.map(a =>
          a.id === asig.id ? actualizada : a
        );
        this.asignando = null;
        this.mostrarNotificacion('Mecánico asignado. Se notificó al cliente.');
      },
      error: (err: any) => {
        this.asignando = null;
        this.mostrarError(err?.error?.detail || 'No se pudo asignar el mecánico.');
      }
    });
  }

  getNombreMecanico(asig: any): string {
    if (asig?.mecanico?.usuario) {
      return `${asig.mecanico.usuario.nombre} ${asig.mecanico.usuario.apellido}`;
    }
    return asig?.mecanico_id ? `Mecánico #${asig.mecanico_id}` : '';
  }

  getDescripcionIncidente(asig: any): string {
    return asig?.incidente?.descripcion || `Incidente #${asig?.incidente_id}`;
  }

  seleccionarAsignacion(asig: any): void {
    this.selectedAsignacion = asig;
    this.nuevoEstado = asig.estado;
    this.view = 'detail';
  }

  actualizarEstado(): void {
    if (!this.selectedAsignacion || !this.nuevoEstado) return;
    this.asignacionService.actualizarEstado(this.selectedAsignacion.id, this.nuevoEstado).subscribe({
      next: () => {
        this.selectedAsignacion.estado = this.nuevoEstado;
      },
      error: () => alert('Error al actualizar el estado')
    });
  }

  getStepStatus(paso: string): 'completed' | 'current' | 'pending' {
    const estadoMap: Record<string, number> = {
      'pendiente': 0, 'taller_asignado': 0, 'Aceptado': 0,
      'en_camino': 1, 'En camino': 1,
      'en_atencion': 2, 'En proceso': 2,
      'finalizado': 3, 'Finalizado': 3,
    };
    const currentIndex = estadoMap[this.selectedAsignacion?.estado] ?? 0;
    const stepIndex = estadoMap[paso] ?? this.pasos.indexOf(paso);
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'current';
    return 'pending';
  }

  volver(): void {
    this.view = 'list';
    this.selectedAsignacion = null;
  }

  // ── Mapa: ubicación del cliente (incidente) ──

  get tieneUbicacion(): boolean {
    const inc = this.selectedAsignacion?.incidente;
    return inc?.latitud != null && inc?.longitud != null;
  }

  abrirEnMapa(): void {
    const inc = this.selectedAsignacion?.incidente;
    if (!inc?.latitud || !inc?.longitud) return;
    // Abre Google Maps en una pestaña nueva con el pin en la ubicación del incidente
    window.open(
      `https://www.google.com/maps?q=${inc.latitud},${inc.longitud}`,
      '_blank'
    );
  }

  private mostrarNotificacion(msg: string): void {
    this.notificacion = msg;
    this.error = null;
    setTimeout(() => (this.notificacion = null), 3500);
  }

  private mostrarError(msg: string): void {
    this.error = msg;
    this.notificacion = null;
    setTimeout(() => (this.error = null), 4000);
  }
}
