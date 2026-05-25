import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ServicioService } from '../../../../core/services/servicio.service';

@Component({
    selector: 'app-servicios-list',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule],
    templateUrl: './servicios-list.component.html'
})
export class ServiciosListComponent implements OnInit {
    private fb = inject(FormBuilder);
    private servicioService = inject(ServicioService);

    servicios: any[] = [];
    loading: boolean = false;
    showModal: boolean = false;

    servicioForm: FormGroup = this.fb.group({
        nombre: ['', [Validators.required]],
        descripcion: ['', [Validators.required]],
        prioridad: [1, [Validators.required, Validators.min(1)]]
    });

    ngOnInit(): void {
        this.cargarServicios();
    }

    cargarServicios(): void {
        this.loading = true;
        this.servicioService.getServicios().subscribe({
            next: (data) => {
                this.servicios = data;
                this.loading = false;
            },
            error: () => this.loading = false
        });
    }

    abrirModal(): void { this.showModal = true; }

    cerrarModal(): void {
        this.showModal = false;
        this.servicioForm.reset({ prioridad: 1 });
    }

    guardar(): void {
        if (this.servicioForm.valid) {
            this.loading = true;
            this.servicioService.crearServicio(this.servicioForm.value).subscribe({
                next: () => {
                    this.cargarServicios();
                    this.cerrarModal();
                    this.loading = false;
                },
                error: (err) => {
                    this.loading = false;
                    alert('Error al guardar el servicio.');
                }
            });
        }
    }

    borrarServicio(id: number): void {
        if (confirm('¿Deseas eliminar este servicio?')) {
            this.servicioService.eliminarServicio(id).subscribe({
                next: () => this.servicios = this.servicios.filter(s => s.id !== id),
                error: () => alert('Error al borrar el servicio.')
            });
        }
    }
}
