import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { VehiculoService } from '../../../../core/services/vehiculo.service';
import { Vehiculo } from '../../../../core/models/vehiculo.model';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { 
  heroTruck, 
  heroMagnifyingGlass, 
  heroEye, 
  heroTrash, 
  heroChevronLeft, 
  heroChevronRight,
  heroIdentification
} from '@ng-icons/heroicons/outline';

@Component({
  selector: 'app-vehiculos-gestion',
  standalone: true,
  imports: [CommonModule, FormsModule, NgIconComponent],
  templateUrl: './vehiculos-gestion.component.html',
  viewProviders: [provideIcons({ 
    heroTruck, 
    heroMagnifyingGlass, 
    heroEye, 
    heroTrash, 
    heroChevronLeft, 
    heroChevronRight,
    heroIdentification
  })]
})
export class VehiculosGestionComponent implements OnInit {
  private vehiculoService = inject(VehiculoService);

  protected Math = Math;

  // State
  vehiculos = signal<Vehiculo[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);

  // Filters
  searchUserId = signal<string>('');
  searchPlate = signal<string>('');

  // Pagination
  currentPage = signal(1);
  pageSize = signal(10);

  // Computed
  filteredVehiculos = computed(() => {
    let list = this.vehiculos();
    
    if (this.searchUserId()) {
      const userId = Number(this.searchUserId());
      if (!isNaN(userId)) {
        list = list.filter(v => v.cliente_id === userId);
      }
    }

    if (this.searchPlate()) {
      const term = this.searchPlate().toLowerCase();
      list = list.filter(v => v.placa.toLowerCase().includes(term));
    }

    return list;
  });

  paginatedVehiculos = computed(() => {
    const start = (this.currentPage() - 1) * this.pageSize();
    return this.filteredVehiculos().slice(start, start + this.pageSize());
  });

  totalPages = computed(() => {
    return Math.ceil(this.filteredVehiculos().length / this.pageSize());
  });

  ngOnInit(): void {
    this.loadVehiculos();
  }

  loadVehiculos() {
    this.loading.set(true);
    this.vehiculoService.getAllVehiculos().subscribe({
      next: (data) => {
        this.vehiculos.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        console.error(err);
        this.error.set('Error al cargar la flota de vehículos.');
        this.loading.set(false);
      }
    });
  }

  onDelete(id: number) {
    if (confirm('¿Estás seguro de eliminar este vehículo?')) {
      this.vehiculoService.eliminarVehiculo(id).subscribe(() => {
        this.loadVehiculos();
      });
    }
  }
}
