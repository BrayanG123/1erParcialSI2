import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminOpsService } from '../../../../core/services/admin-ops.service';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-disponibilidad',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './disponibilidad.component.html'
})
export class DisponibilidadComponent implements OnInit {
  private adminOpsService = inject(AdminOpsService);

  loading = false;
  tallerDisponible = true;
  
  // Métricas
  tecnicosDisponibles = 0;
  tecnicosTotales = 0;
  serviciosActivos = 0;
  capacidadMaxima = 10;
  
  tecnicosList: any[] = [];

  ngOnInit(): void {
    this.cargarDisponibilidad();
  }

  cargarDisponibilidad(): void {
    this.loading = true;
    
    forkJoin({
      usuarios: this.adminOpsService.getUsuariosAdmin(),
      asignaciones: this.adminOpsService.getAsignaciones()
    }).subscribe({
      next: (data) => {
        const mecanicos = data.usuarios.filter(u => u.rol === 'mecanico');
        this.tecnicosTotales = mecanicos.length;
        this.serviciosActivos = data.asignaciones.filter(a => a.estado !== 'Finalizado').length;
        
        // Mapear técnicos con su estado y ubicación
        this.tecnicosList = mecanicos.map(m => {
          const asignacionActiva = data.asignaciones.find(a => a.mecanico_id === m.id && a.estado !== 'Finalizado');
          const estado = asignacionActiva ? 'En servicio' : 'Disponible';
          
          return {
            nombre: `${m.nombre} ${m.apellido}`,
            estado: estado,
            ubicacion: estado === 'En servicio' ? 'Av. 68 con Calle 80' : 'Taller',
            lat: 4.60, // Mock
            lng: -74.07 // Mock
          };
        });

        this.tecnicosDisponibles = this.tecnicosList.filter(t => t.estado === 'Disponible').length;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  getPorcentajeOcupacion(): number {
    return (this.serviciosActivos / this.capacidadMaxima) * 100;
  }

  toggleDisponibilidad(): void {
    // Aquí se llamaría a un servicio para actualizar el estado del taller
    console.log('Taller disponible:', this.tallerDisponible);
  }

  verEnMapa(tecnico: any): void {
    alert(`Abriendo mapa para ${tecnico.nombre} en ${tecnico.ubicacion}`);
  }
}
