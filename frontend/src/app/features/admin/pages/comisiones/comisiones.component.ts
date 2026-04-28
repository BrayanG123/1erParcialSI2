import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { AdminOpsService } from '../../../../core/services/admin-ops.service';
import { Comision_Servicio } from '../../../../core/models/admin-ops.model';

@Component({
  selector: 'app-comisiones',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './comisiones.component.html'
})
export class ComisionesComponent implements OnInit {
  private adminOpsService = inject(AdminOpsService);

  comisiones: Comision_Servicio[] = [];
  loading = false;
  error: string | null = null;

  ngOnInit(): void {
    this.cargarComisiones();
  }

  cargarComisiones(): void {
    this.loading = true;
    this.error = null;
    this.adminOpsService.getComisiones().subscribe({
      next: (data) => {
        this.comisiones = Array.isArray(data) ? data : [];
        this.loading = false;
      },
      error: () => {
        this.comisiones = [];
        this.error = 'No se pudieron cargar las comisiones.';
        this.loading = false;
      }
    });
  }
}
