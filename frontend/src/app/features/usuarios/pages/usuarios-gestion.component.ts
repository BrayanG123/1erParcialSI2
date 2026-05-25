import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { SuperadminService } from '../../../core/services/superadmin.service';
import { AdminOpsService } from '../../../core/services/admin-ops.service';
import { RoleService } from '../../../core/auth/services/role.service';
import { Usuario, RolUsuario } from '../models/usuario.model';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { 
  heroMagnifyingGlass, 
  heroPencilSquare, 
  heroPauseCircle, 
  heroTrash, 
  heroChevronLeft, 
  heroChevronRight,
  heroUser,
  heroXMark
} from '@ng-icons/heroicons/outline';

@Component({
  selector: 'app-usuarios-gestion',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, NgIconComponent],
  templateUrl: './usuarios-gestion.component.html',
  styleUrl: './usuarios-gestion.component.css',
  viewProviders: [provideIcons({ 
    heroMagnifyingGlass, 
    heroPencilSquare, 
    heroPauseCircle, 
    heroTrash, 
    heroChevronLeft, 
    heroChevronRight,
    heroUser,
    heroXMark
  })]
})
export class UsuariosGestionComponent implements OnInit {
  private superadminService = inject(SuperadminService);
  private adminService = inject(AdminOpsService);
  private roleService = inject(RoleService);
  private fb = inject(FormBuilder);

  protected Math = Math;

  // State
  usuarios = signal<Usuario[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);
  showModal = signal(false);
  submitting = signal(false);

  // Form
  userForm: FormGroup = this.fb.group({
    nombre: ['', [Validators.required, Validators.minLength(2)]],
    apellido: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    rol: ['cliente', [Validators.required]]
  });

  // Filters
  searchTerm = signal('');
  selectedRol = signal<string>('todos');

  // Pagination
  currentPage = signal(1);
  pageSize = signal(10);

  // Computed
  filteredUsuarios = computed(() => {
    let list = this.usuarios();
    
    if (this.searchTerm()) {
      const term = this.searchTerm().toLowerCase();
      list = list.filter(u => 
        u.nombre.toLowerCase().includes(term) || 
        u.apellido.toLowerCase().includes(term) || 
        u.email.toLowerCase().includes(term) ||
        u.username.toLowerCase().includes(term)
      );
    }

    if (this.selectedRol() !== 'todos') {
      list = list.filter(u => u.rol === this.selectedRol());
    }

    return list;
  });

  paginatedUsuarios = computed(() => {
    const start = (this.currentPage() - 1) * this.pageSize();
    return this.filteredUsuarios().slice(start, start + this.pageSize());
  });

  totalPages = computed(() => {
    return Math.ceil(this.filteredUsuarios().length / this.pageSize());
  });

  ngOnInit(): void {
    this.loadUsuarios();
  }

  loadUsuarios() {
    this.loading.set(true);
    this.error.set(null);

    const request = this.roleService.isSuperAdmin() 
      ? this.superadminService.getUsuarios()
      : this.adminService.getUsuariosAdmin();

    request.subscribe({
      next: (data) => {
        this.usuarios.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set('Error al cargar los usuarios.');
        this.loading.set(false);
        console.error(err);
      }
    });
  }

  // Modal logic
  openModal() {
    this.userForm.reset({ rol: 'cliente' });
    this.showModal.set(true);
  }

  closeModal() {
    this.showModal.set(false);
  }

  onSubmit() {
    if (this.userForm.invalid) {
      this.userForm.markAllAsTouched();
      return;
    }

    this.submitting.set(true);

    // Mapeo de datos: Generamos username a partir del email
    const formValue = this.userForm.value;
    const payload = {
      ...formValue,
      username: formValue.email.split('@')[0].replace(/[^a-zA-Z0-9_]/g, '_')
    };

    const request = this.roleService.isSuperAdmin()
      ? this.superadminService.createUser(payload)
      : this.adminService.createMecanico(payload);

    request.subscribe({
      next: () => {
        alert('Usuario creado correctamente');
        this.submitting.set(false);
        this.closeModal();
        this.loadUsuarios();
      },
      error: (err: any) => {
        console.error('Error en registro:', err);
        const msg = err.error?.detail?.[0]?.msg || err.error?.detail || 'Error al crear el usuario';
        alert(`Fallo en el registro: ${msg}`);
        this.submitting.set(false);
      }
    });
  }

  // Actions
  onEdit(usuario: Usuario) {
    console.log('Editar usuario', usuario);
    // Implement logic or modal
  }

  onSuspend(usuario: Usuario) {
    if (confirm(`¿Estás seguro de que deseas suspender a ${usuario.nombre}?`)) {
      this.superadminService.suspendUsuario(usuario.id).subscribe({
        next: () => {
          this.loadUsuarios();
        },
        error: (err) => alert('Error al suspender usuario')
      });
    }
  }

  onDelete(usuario: Usuario) {
    if (confirm(`¿Estás seguro de que deseas eliminar a ${usuario.nombre}? Esta acción no se puede deshacer.`)) {
      this.superadminService.deleteUsuario(usuario.id).subscribe({
        next: () => {
          this.loadUsuarios();
        },
        error: (err) => alert('Error al eliminar usuario')
      });
    }
  }

  // Helpers
  getRolBadgeClass(rol: string): string {
    switch (rol) {
      case 'superadmin': 
        return 'bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-500/10 dark:text-purple-400 dark:border-purple-500/20';
      case 'administrador': 
        return 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20';
      case 'mecanico': 
        return 'bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-500/10 dark:text-orange-400 dark:border-orange-500/20';
      case 'cliente': 
        return 'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20';
      default: 
        return 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-500/10 dark:text-slate-400 dark:border-slate-500/20';
    }
  }
}
