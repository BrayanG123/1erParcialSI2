import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { CategoriaService } from '../services/categoria.service';
import { Categoria_Item } from '../models/categoria.model';
import { RoleService } from '../../../core/auth/services/role.service';

@Component({
  selector: 'app-categorias',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './categorias.component.html'
})
export class CategoriasComponent implements OnInit {
  private categoriaService = inject(CategoriaService);
  private roleService = inject(RoleService);
  private fb = inject(FormBuilder);

  categorias: Categoria_Item[] = [];
  loading = false;
  show_modal = false;
  error: string | null = null;
  editingId: number | null = null;

  // ✅ true solo si es superadmin
  isSuperAdmin = false;

  form = this.fb.group({
    nombre: ['', [Validators.required, Validators.minLength(2)]],
    descripcion: [''],
    prioridad: [1, [Validators.required, Validators.min(1), Validators.max(3)]]
  });

  ngOnInit(): void {
    this.isSuperAdmin = this.roleService.isSuperAdmin();
    this.cargarCategorias();
  }

  cargarCategorias(): void {
    this.loading = true;
    this.error = null;
    this.categoriaService.getCategorias().subscribe({
      next: (data) => {
        this.categorias = Array.isArray(data) ? data : [];
        this.loading = false;
      },
      error: () => {
        this.categorias = [];
        this.error = 'No se pudieron cargar las categorías.';
        this.loading = false;
      }
    });
  }

  abrirModal(): void {
    if (!this.isSuperAdmin) return; // ✅ doble protección
    this.show_modal = true;
  }

  cerrarModal(): void {
    this.show_modal = false;
    this.editingId = null;
    this.form.reset({ nombre: '', descripcion: '', prioridad: 1 });
  }

  guardarCategoria(): void {
    if (!this.isSuperAdmin) return;
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const payload = {
      nombre: String(this.form.value.nombre).trim(),
      descripcion: String(this.form.value.descripcion || '').trim() || undefined,
      prioridad: Number(this.form.value.prioridad)
    };

    const obs = this.editingId 
      ? this.categoriaService.actualizarCategoria(this.editingId, payload)
      : this.categoriaService.crearCategoria(payload);

    obs.subscribe({
      next: () => {
        this.cerrarModal();
        this.cargarCategorias();
      },
      error: (err) => {
        this.error = err?.error?.detail || 'No se pudo guardar la categoría.';
      }
    });
  }

  editarCategoria(cat: Categoria_Item): void {
    if (!this.isSuperAdmin) return;
    this.editingId = cat.id;
    this.form.patchValue({
      nombre: cat.nombre,
      descripcion: cat.descripcion || '',
      prioridad: cat.prioridad
    });
    this.show_modal = true;
  }

  eliminarCategoria(id: number): void {
    if (!this.isSuperAdmin) return;
    if (!confirm('¿Estás seguro de eliminar esta categoría?')) return;

    this.categoriaService.eliminarCategoria(id).subscribe({
      next: () => this.cargarCategorias(),
      error: (err) => this.error = err?.error?.detail || 'No se pudo eliminar.'
    });
  }
}
