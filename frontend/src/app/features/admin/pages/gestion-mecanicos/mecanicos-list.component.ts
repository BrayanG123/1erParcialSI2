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

    mecanicoForm: FormGroup = this.fb.group({
        nombre: ['', [Validators.required, Validators.minLength(3)]],
        especialidad: ['Motor', [Validators.required]],
        telefono: ['', [Validators.required, Validators.pattern('^[0-9]+$')]],
        email: ['', [Validators.required, Validators.email]]
    });

    ngOnInit(): void { this.cargarMecanicos(); }

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

    abrirModal(): void { this.showModal = true; }
    cerrarModal(): void {
        this.showModal = false;
        this.mecanicoForm.reset({ especialidad: 'Motor' });
    }

    guardarMecanico(): void {
        if (this.mecanicoForm.valid) {
            const raw = this.mecanicoForm.value;
            const partes = raw.nombre.trim().split(' ');

            const payload = {
                nombre: partes[0],
                apellido: partes.slice(1).join(' ') || 'S/A',
                email: raw.email,
                username: raw.email.split('@')[0],
                password: 'Mecanico123*', // Password por defecto
                rol: 'mecanico'
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
                    alert('Error al registrar el mecánico.');
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
        // Lógica de edición - podríamos abrir el mismo modal con datos precargados
        this.mecanicoForm.patchValue({
            nombre: `${m.nombre} ${m.apellido}`,
            email: m.email,
            telefono: m.telefono || ''
        });
        this.showModal = true;
    }
}
