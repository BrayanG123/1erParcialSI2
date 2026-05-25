import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AdminOpsService } from '../../../../core/services/admin-ops.service';
import { Servicio_Realizado } from '../../../../core/models/admin-ops.model';

@Component({
  selector: 'app-servicios-realizados',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './servicios-realizados.component.html'
})
export class ServiciosRealizadosComponent implements OnInit {
  private adminOpsService = inject(AdminOpsService);
  private router = inject(Router);

  servicios_realizados: Servicio_Realizado[] = [];
  loading = false;
  error: string | null = null;

  // Filtros
  fechaInicio: string = '';
  fechaFin: string = '';
  estadoFiltro: string = 'Todos';
  searchTerm: string = '';

  ngOnInit(): void {
    this.cargarServiciosRealizados();
  }

  cargarServiciosRealizados(): void {
    this.loading = true;
    this.error = null;
    this.adminOpsService.getServiciosRealizados().subscribe({
      next: (data) => {
        this.servicios_realizados = Array.isArray(data) ? data : [];
        this.loading = false;
      },
      error: () => {
        this.servicios_realizados = [];
        this.error = 'No se pudo cargar la lista de servicios realizados.';
        this.loading = false;
      }
    });
  }

  getFilteredServicios() {
    return this.servicios_realizados.filter(s => {
      const matchSearch = !this.searchTerm || 
        s.id.toString().includes(this.searchTerm) || 
        (s.descripcion || '').toLowerCase().includes(this.searchTerm.toLowerCase());
      
      const matchEstado = this.estadoFiltro === 'Todos' || s.estado === this.estadoFiltro;
      
      // Filtros de fecha (simplificado)
      return matchSearch && matchEstado;
    });
  }

  formatServicioId(id: number): string {
    return `#SER-2024-${id.toString().padStart(5, '0')}`;
  }

  formatCurrency(value: number | undefined): string {
    if (value === undefined) return '$0';
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(value);
  }

  verDetalle(id: number): void {
    // Por ahora redirigimos a evidencias del incidente ligado si es posible
    // O mostramos un alert con el ID
    alert(`Viendo detalle del servicio ${this.formatServicioId(id)}`);
  }
}
