import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { SuperadminService } from '../../../core/services/superadmin.service';
import { TallerGlobalRow } from '../models/taller.model';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { 
  heroBuildingOffice2, 
  heroPlus, 
  heroMagnifyingGlass, 
  heroFunnel, 
  heroPencilSquare, 
  heroNoSymbol, 
  heroChevronLeft, 
  heroChevronRight,
  heroMapPin,
  heroPhone,
  heroClock,
  heroEnvelope
} from '@ng-icons/heroicons/outline';

@Component({
  selector: 'app-talleres-gestion',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, NgIconComponent],
  templateUrl: './talleres-gestion.component.html',
  viewProviders: [provideIcons({ 
    heroBuildingOffice2, 
    heroPlus, 
    heroMagnifyingGlass, 
    heroFunnel, 
    heroPencilSquare, 
    heroNoSymbol, 
    heroChevronLeft, 
    heroChevronRight,
    heroMapPin,
    heroPhone,
    heroClock,
    heroEnvelope
  })]
})
export class TalleresGestionComponent implements OnInit {
  private superadminService = inject(SuperadminService);
  private fb = inject(FormBuilder);

  protected readonly Math = Math;

  // State
  talleres = signal<TallerGlobalRow[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);
  showModal = signal(false);
  submitting = signal(false);

  // Form
  tallerForm: FormGroup = this.fb.group({
    nombre: ['', [Validators.required, Validators.minLength(3)]],
    direccion: ['', [Validators.required, Validators.minLength(5)]],
    telefono: ['', [Validators.required]],
    latitud: [null],
    longitud: [null]
  });

  // Filters
  searchTerm = signal('');
  statusFilter = signal('todos');

  // Pagination
  currentPage = signal(1);
  pageSize = signal(8);

  // Computed
  filteredTalleres = computed(() => {
    let list = this.talleres();

    if (this.statusFilter() !== 'todos') {
      const active = this.statusFilter() === 'activo';
      list = list.filter(t => t.is_active === active);
    }

    if (this.searchTerm()) {
      const term = this.searchTerm().toLowerCase();
      list = list.filter(t => 
        t.nombre.toLowerCase().includes(term) || 
        t.direccion.toLowerCase().includes(term) ||
        t.telefono?.toLowerCase().includes(term)
      );
    }

    return list;
  });

  paginatedTalleres = computed(() => {
    const start = (this.currentPage() - 1) * this.pageSize();
    return this.filteredTalleres().slice(start, start + this.pageSize());
  });

  totalPages = computed(() => {
    return Math.ceil(this.filteredTalleres().length / this.pageSize());
  });

  ngOnInit(): void {
    this.loadTalleres();
  }

  loadTalleres() {
    this.loading.set(true);
    this.superadminService.getTalleres().subscribe({
      next: (data) => {
        this.talleres.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar los talleres.');
        this.loading.set(false);
      }
    });
  }

  // Modal logic
  openModal() {
    this.tallerForm.reset();
    this.showModal.set(true);
  }

  closeModal() {
    this.showModal.set(false);
  }

  onSubmitTaller() {
    if (this.tallerForm.invalid) {
      this.tallerForm.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    this.superadminService.createTaller(this.tallerForm.value).subscribe({
      next: () => {
        alert('Taller registrado correctamente');
        this.submitting.set(false);
        this.closeModal();
        this.loadTalleres();
      },
      error: (err: any) => {
        console.error(err);
        alert('Error al registrar el taller');
        this.submitting.set(false);
      }
    });
  }

  toggleEstado(taller: TallerGlobalRow) {
    const nuevoEstado = !taller.is_active;
    this.superadminService.updateTaller(taller.id, { is_active: nuevoEstado }).subscribe({
      next: () => {
        this.loadTalleres();
      },
      error: (err: any) => {
        console.error(err);
        alert('Error al actualizar el estado del taller.');
      }
    });
  }

  onEdit(taller: TallerGlobalRow) {
    // Lógica para abrir modal de edición (futura implementación)
    console.log('Editar taller:', taller);
  }
}
