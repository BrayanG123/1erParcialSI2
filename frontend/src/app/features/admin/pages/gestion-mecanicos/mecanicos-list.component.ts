import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AdminOpsService } from '../../../../core/services/admin-ops.service';

@Component({
    selector: 'app-mecanicos-list',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule],
    templateUrl: './mecanicos-list.component.html'
})
export class MecanicosListComponent implements OnInit {
    private fb = inject(FormBuilder);
    private adminOpsService = inject(AdminOpsService);

    mecanicos: any[] = [];
    loading: boolean = false;
    showModal: boolean = false;

    // ── Especialidades (multiselección) ──
    catalogoEspecialidades: string[] = [];
    especialidadesSeleccionadas: string[] = [];
    // null = creando un técnico nuevo | objeto = editando sus especialidades
    mecanicoEnEdicion: any | null = null;

    mecanicoForm: FormGroup = this.fb.group({
        nombre: ['', [Validators.required, Validators.minLength(3)]],
        telefono: ['', [Validators.required, Validators.pattern('^[0-9]+$')]],
        email: ['', [Validators.required, Validators.email]]
    });

    ngOnInit(): void {
        this.cargarMecanicos();
        this.cargarCatalogo();
    }

    private cargarCatalogo(): void {
        this.adminOpsService.getCatalogoEspecialidades().subscribe({
            next: (res) => (this.catalogoEspecialidades = res.especialidades),
            // Fallback por si el backend no responde (mismo catálogo canónico)
            error: () => (this.catalogoEspecialidades = [
                'Motor y transmisión', 'Sistema eléctrico', 'Frenos y dirección',
                'Llantas y suspensión', 'Chapería y pintura', 'Aire acondicionado',
                'Diagnóstico general', 'Auxilio en ruta',
            ])
        });
    }

    toggleEspecialidad(esp: string): void {
        const idx = this.especialidadesSeleccionadas.indexOf(esp);
        idx >= 0
            ? this.especialidadesSeleccionadas.splice(idx, 1)
            : this.especialidadesSeleccionadas.push(esp);
    }

    cargarMecanicos(): void {
        this.loading = true;
        
        // Cargamos usuarios y asignaciones en paralelo
        this.adminOpsService.getUsuariosAdmin().subscribe({
            next: (usuarios) => {
                this.adminOpsService.getAsignaciones().subscribe({
                    next: (asignaciones) => {
                        this.mecanicos = usuarios
                            .filter((u: any) => u.rol === 'mecanico')
                            .map((m: any) => {
                                const activeAssignments = asignaciones.filter((a: any) => 
                                    a.mecanico_id === m.id && (a.estado === 'en_proceso' || a.estado === 'asignado')
                                );
                                
                                return {
                                    ...m,
                                    servicios_activos: activeAssignments.length,
                                    disponibilidad: this.calcularDisponibilidad(m, activeAssignments.length),
                                    estado: 'Activo', // Por defecto activo
                                    telefono: m.telefono || '310 987 6543' // Fallback si no hay teléfono
                                };
                            });
                        this.loading = false;
                    },
                    error: () => {
                        this.loading = false;
                        this.mecanicos = [];
                    }
                });
            },
            error: () => {
                this.loading = false;
                this.mecanicos = [];
            }
        });
    }

    private calcularDisponibilidad(mecanico: any, activeCount: number): string {
        if (activeCount > 0) return 'En servicio';
        // Podríamos añadir lógica para 'No disponible' basada en algún campo de horario
        return 'Disponible';
    }

    abrirModal(): void {
        this.mecanicoEnEdicion = null;
        this.especialidadesSeleccionadas = [];
        this.showModal = true;
    }

    cerrarModal(): void {
        this.showModal = false;
        this.mecanicoEnEdicion = null;
        this.especialidadesSeleccionadas = [];
        this.mecanicoForm.reset();
    }

    guardarMecanico(): void {
        // ── Modo edición: solo se actualizan las especialidades ──
        if (this.mecanicoEnEdicion) {
            const perfilId = this.mecanicoEnEdicion.perfil_mecanico?.id;
            if (!perfilId) {
                alert('Este usuario no tiene perfil de mecánico.');
                return;
            }
            this.loading = true;
            this.adminOpsService
                .actualizarEspecialidades(perfilId, this.especialidadesSeleccionadas)
                .subscribe({
                    next: (perfilActualizado) => {
                        // Refrescar el registro en la lista local sin recargar todo
                        this.mecanicoEnEdicion.perfil_mecanico = {
                            ...this.mecanicoEnEdicion.perfil_mecanico,
                            ...perfilActualizado,
                        };
                        this.loading = false;
                        this.cerrarModal();
                    },
                    error: (err) => {
                        this.loading = false;
                        alert(err?.error?.detail || 'Error al actualizar las especialidades.');
                    }
                });
            return;
        }

        // ── Modo creación ──
        if (this.mecanicoForm.valid) {
            if (this.especialidadesSeleccionadas.length === 0) {
                alert('Selecciona al menos una especialidad para el técnico.');
                return;
            }
            const raw = this.mecanicoForm.value;
            const partes = raw.nombre.trim().split(' ');

            const payload = {
                nombre: partes[0],
                apellido: partes.slice(1).join(' ') || 'S/A',
                email: raw.email,
                username: raw.email.split('@')[0],
                password: 'Mecanico123*', // Password por defecto
                rol: 'mecanico',
                // El backend las guarda en el perfil del mecánico (puede ser más de una)
                especialidades: this.especialidadesSeleccionadas,
            };

            this.loading = true;
            this.adminOpsService.createMecanico(payload).subscribe({
                next: () => {
                    this.cargarMecanicos();
                    this.cerrarModal();
                    alert('Mecánico registrado!');
                },
                error: (err) => {
                    this.loading = false;
                    alert(err?.error?.detail || 'Error al registrar el mecánico.');
                }
            });
        }
    }

    borrar(id: number): void {
        if (confirm('¿Eliminar a este técnico?')) {
            this.adminOpsService.eliminarMecanico(id).subscribe({
                next: () => {
                    this.mecanicos = this.mecanicos.filter(m => m.id !== id);
                },
                error: () => alert('Error al borrar el mecánico.')
            });
        }
    }

    editar(m: any): void {
        // Edición: por ahora solo las ESPECIALIDADES del técnico
        // (los datos personales los gestiona el propio usuario en su perfil)
        this.mecanicoEnEdicion = m;
        this.especialidadesSeleccionadas = [...(m.perfil_mecanico?.especialidades ?? [])];
        this.showModal = true;
    }
}
