import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { EvidenciaService, Evidencia } from '../../../../core/services/evidencia.service';
import { IncidenteService } from '../../../../core/services/incidente.service';
import { Incidente } from '../../../../core/models/incidente.model';

@Component({
  selector: 'app-evidencias',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './evidencias.component.html',
  styleUrls: ['./evidencias.component.css']
})
export class EvidenciasComponent implements OnInit {
  private evidenciaService = inject(EvidenciaService);
  private incidenteService = inject(IncidenteService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  incidenteId: number | null = null;
  incidente: Incidente | null = null;
  evidencias: Evidencia[] = [];
  loading = false;
  error: string | null = null;
  selectedImage: Evidencia | null = null;

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.incidenteId = parseInt(idParam);
      this.cargarDatos();
    } else {
      this.error = 'No se especificó un incidente válido';
    }
  }

  cargarDatos(): void {
    if (!this.incidenteId) return;
    this.loading = true;

    // Cargar incidente
    this.incidenteService.getIncidenteById(this.incidenteId).subscribe({
      next: (inc) => {
        this.incidente = inc;
        
        // Cargar evidencias
        this.evidenciaService.getEvidenciasByIncidente(this.incidenteId!).subscribe({
          next: (evs) => {
            this.evidencias = evs;
            this.loading = false;
          },
          error: () => {
            this.loading = false;
          }
        });
      },
      error: (err) => {
        this.error = 'No se pudo cargar la información del incidente';
        this.loading = false;
      }
    });
  }

  getEvidenciasTipo(tipo: 'foto' | 'audio'): Evidencia[] {
    return this.evidencias.filter(e => e.tipo === tipo);
  }

  aceptarSolicitud(): void {
    if (!this.incidenteId) return;
    if (confirm('¿Deseas aceptar esta solicitud? Pasarás a la pantalla de asignación.')) {
      // Aquí podríamos actualizar el estado a 'aceptado' si existiera, 
      // pero por ahora volvemos a la lista para asignar
      this.router.navigate(['/admin/incidentes']);
    }
  }

  rechazarSolicitud(): void {
    if (!this.incidenteId) return;
    if (confirm('¿Estás seguro de rechazar esta solicitud?')) {
      this.incidenteService.actualizarIncidente(this.incidenteId, { estado: 'rechazado' }).subscribe({
        next: () => {
          alert('Solicitud rechazada');
          this.router.navigate(['/admin/incidentes']);
        },
        error: () => alert('Error al rechazar la solicitud')
      });
    }
  }

  abrirLightbox(evidencia: Evidencia): void {
    if (evidencia.tipo === 'foto') this.selectedImage = evidencia;
  }

  cerrarLightbox(): void {
    this.selectedImage = null;
  }
}
