import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { AdminOpsService } from '../../../../core/services/admin-ops.service';
import { Evidencia_Item } from '../../../../core/models/admin-ops.model';

@Component({
  selector: 'app-seguimiento',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './seguimiento.component.html'
})
export class SeguimientoComponent implements OnInit {
  private adminOpsService = inject(AdminOpsService);

  asignaciones_en_proceso: any[] = [];
  evidencias: Evidencia_Item[] = [];

  asignacion_activa: any | null = null;
  loading_asignaciones = false;
  loading_evidencias = false;
  error: string | null = null;

  ngOnInit(): void {
    this.cargarAsignacionesEnProceso();
  }

  cargarAsignacionesEnProceso(): void {
    this.loading_asignaciones = true;
    this.adminOpsService.getAsignaciones().subscribe({
      next: (data) => {
        const listado = Array.isArray(data) ? data : [];
        this.asignaciones_en_proceso = listado.filter(
          (asignacion) => String(asignacion?.estado || '').toLowerCase() === 'en proceso'
        );
        this.loading_asignaciones = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar las asignaciones en proceso.';
        this.loading_asignaciones = false;
      }
    });
  }

  seleccionarServicio(asignacion: any): void {
    this.asignacion_activa = asignacion;
    this.evidencias = [];
    this.loading_evidencias = true;
    this.error = null;

    const incidente_id = Number(asignacion?.incidente_id || asignacion?.incidente?.id);
    if (!incidente_id) {
      this.error = 'La asignación no tiene incidente asociado.';
      this.loading_evidencias = false;
      return;
    }

    this.adminOpsService.getEvidenciasPorIncidente(incidente_id).subscribe({
      next: (data) => {
        this.evidencias = Array.isArray(data) ? data : [];
        this.loading_evidencias = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar evidencias para este incidente.';
        this.loading_evidencias = false;
      }
    });
  }

  getEvidenciaUrl(item: Evidencia_Item): string {
    return item.url || item.archivo_url || item.imagen_url || item.foto_url || '';
  }
}
