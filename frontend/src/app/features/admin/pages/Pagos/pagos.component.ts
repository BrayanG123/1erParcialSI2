import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AdminOpsService } from '../../../../core/services/admin-ops.service';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-pagos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './pagos.component.html'
})
export class PagosComponent implements OnInit {
  private adminOpsService = inject(AdminOpsService);

  loading = false;
  filtroFecha = 'mes'; // 'semana' | 'mes' | 'año'
  
  // Datos
  registros: any[] = [];
  
  // Resumen
  resumen = {
    ingresosTotales: 0,
    comisionesPlataforma: 0,
    netoRecibir: 0,
    pendientePago: 0
  };

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.loading = true;
    
    // Cargamos pagos y comisiones
    forkJoin({
      pagos: this.adminOpsService.getPagos(),
      comisiones: this.adminOpsService.getComisiones(),
      servicios: this.adminOpsService.getServiciosRealizados()
    }).subscribe({
      next: (data) => {
        this.procesarDatos(data);
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  private procesarDatos(data: { pagos: any[], comisiones: any[], servicios: any[] }): void {
    // Fusionamos la información por servicio
    this.registros = data.servicios.map(servicio => {
      const pago = data.pagos.find(p => p.servicio_id === servicio.id);
      const comision = data.comisiones.find(c => c.servicio_id === servicio.id);
      
      const bruto = servicio.costo_final || 0;
      const montoComision = bruto * 0.10; // 10% fijo como pidió el usuario
      const neto = bruto - montoComision;

      return {
        id: servicio.id,
        fecha: servicio.fecha_realizado || new Date(),
        servicios_count: 1, // En este diseño cada fila es un servicio, pero podríamos agrupar por fecha
        ingresos_brutos: bruto,
        comision_monto: montoComision,
        neto: neto,
        estado: pago ? 'Pagado' : 'Pendiente',
        pago_detalle: pago
      };
    });

    this.calcularTotales();
  }

  calcularTotales(): void {
    this.resumen.ingresosTotales = this.registros.reduce((acc, curr) => acc + curr.ingresos_brutos, 0);
    this.resumen.comisionesPlataforma = this.registros.reduce((acc, curr) => acc + curr.comision_monto, 0);
    this.resumen.netoRecibir = this.resumen.ingresosTotales - this.resumen.comisionesPlataforma;
    this.resumen.pendientePago = this.registros
      .filter(r => r.estado === 'Pendiente')
      .reduce((acc, curr) => acc + curr.neto, 0);
  }

  getFilteredRegistros() {
    // Aquí se aplicaría el filtro por fecha
    return this.registros;
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(value);
  }
}
