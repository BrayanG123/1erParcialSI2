import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IncidenteService } from '../../../../core/services/incidente.service';
import { AsignacionService } from '../../../../core/services/asignacion.service';
import { WebPushService } from '../../../../core/services/web-push.service';

@Component({
  selector: 'app-incidentes-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: '../incidentes/incidentes-list.component.html'
})
export class IncidentesListComponent implements OnInit {
  private incidenteService = inject(IncidenteService);
  private asignacionService = inject(AsignacionService);
  private webPushService = inject(WebPushService);

  incidentesPendientes: any[] = [];
  loading = false;
  notificacion: string | null = null;
  error: string | null = null;

  searchTerm = '';
  filtroPrioridad = '';
  filtroDistancia = '50';
  mostrarBannerNotif = false;

  // Orden y paginación (cliente)
  ordenRecientes = true;
  pagina = 1;
  tamanoPagina = 10;
  probandoPushId: number | null = null;
  Math = Math; // para usar Math.min en el template

  ngOnInit(): void {
    this.mostrarBannerNotif = !this.webPushService.yaSuscrito && this.webPushService.estaDisponible;
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.loading = true;
    this.incidenteService.getIncidentesDisponibles().subscribe({
      next: (data) => {
        this.incidentesPendientes = (Array.isArray(data) ? data : [])
          .sort((a: any, b: any) =>
            new Date(b.fecha_hora ?? b.fecha_creacion ?? 0).getTime() -
            new Date(a.fecha_hora ?? a.fecha_creacion ?? 0).getTime()
          );
        this.loading = false;
      },
      error: () => {
        this.incidentesPendientes = [];
        this.loading = false;
      }
    });
  }

  getFilteredIncidentes(): any[] {
    const factor = this.ordenRecientes ? -1 : 1;
    return this.incidentesPendientes
      .filter((inc: any) => {
        const matchesSearch = !this.searchTerm ||
          (inc.descripcion ?? '').toLowerCase().includes(this.searchTerm.toLowerCase());
        const matchesPrioridad = !this.filtroPrioridad || inc.prioridad === this.filtroPrioridad;
        return matchesSearch && matchesPrioridad;
      })
      .sort((a: any, b: any) =>
        factor * (new Date(a.fecha_hora ?? a.fecha_creacion ?? 0).getTime() -
                  new Date(b.fecha_hora ?? b.fecha_creacion ?? 0).getTime())
      );
  }

  // ── Paginación ──────────────────────────────────────────────

  getIncidentesPagina(): any[] {
    const inicio = (this.pagina - 1) * this.tamanoPagina;
    return this.getFilteredIncidentes().slice(inicio, inicio + this.tamanoPagina);
  }

  get totalPaginas(): number {
    return Math.max(1, Math.ceil(this.getFilteredIncidentes().length / this.tamanoPagina));
  }

  cambiarPagina(delta: number): void {
    const nueva = this.pagina + delta;
    if (nueva < 1 || nueva > this.totalPaginas) return;
    this.pagina = nueva;
  }

  resetPagina(): void {
    this.pagina = 1;
  }

  toggleOrden(): void {
    this.ordenRecientes = !this.ordenRecientes;
    this.pagina = 1;
  }

  // ── DEBUG: prueba de notificación push al cliente ───────────

  probarNotificacion(inc: any): void {
    this.probandoPushId = inc.id;
    console.group(`🔔 [TEST PUSH] Incidente #${inc.id}`);
    console.log('Enviando prueba de push al cliente del incidente...', inc);

    this.asignacionService.probarPushCliente(inc.id).subscribe({
      next: (diag: any) => {
        this.probandoPushId = null;
        console.log('📋 Diagnóstico completo del backend:', diag);
        console.log('  • Cliente:', diag.cliente_nombre, `(usuario_id=${diag.cliente_usuario_id})`);
        console.log('  • firebase-admin instalado:', diag.firebase_admin_instalado);
        console.log('  • Firebase inicializado:', diag.firebase_inicializado);
        console.log('  • Cliente tiene push_token:', diag.tiene_push_token);
        if (diag.push_token_preview) console.log('  • Token (preview):', diag.push_token_preview);
        if ('push_enviado' in diag) console.log('  • Push enviado a FCM:', diag.push_enviado);
        console.log('%c➡ CONCLUSIÓN: ' + (diag.conclusion ?? diag.error ?? 'sin conclusión'),
          'font-weight:bold; color:' + (diag.push_enviado ? 'green' : 'red'));
        console.groupEnd();

        if (diag.push_enviado) {
          this.mostrarNotificacion('✅ Push de prueba enviado. Revisa el celular del cliente.');
        } else {
          this.mostrarError('❌ ' + (diag.conclusion ?? diag.error ?? 'Falló el envío. Ver consola.'));
        }
      },
      error: (err: any) => {
        this.probandoPushId = null;
        console.error('❌ Error HTTP llamando al endpoint de prueba:', err);
        console.groupEnd();
        this.mostrarError(err?.error?.detail || 'Error al probar la notificación.');
      }
    });
  }

  aceptarIncidente(incidenteId: number): void {
    this.asignacionService.crearAsignacion({ incidente_id: incidenteId }).subscribe({
      next: () => {
        this.incidentesPendientes = this.incidentesPendientes.filter(i => i.id !== incidenteId);
        this.mostrarNotificacion('Solicitud aceptada. Ya aparece en Asignaciones de Servicio.');
      },
      error: (err: any) => {
        this.mostrarError(err?.error?.detail || 'No se pudo aceptar la solicitud.');
      }
    });
  }

  rechazarIncidente(incidenteId: number): void {
    this.incidentesPendientes = this.incidentesPendientes.filter(i => i.id !== incidenteId);
    this.mostrarNotificacion('Solicitud descartada de tu lista.');
  }

  verDetalle(inc: any): void {
    console.log('Detalle incidente:', inc);
  }

  activarNotificaciones(): void {
    this.webPushService.suscribir().subscribe({
      complete: () => { this.mostrarBannerNotif = false; }
    });
  }

  rechazarNotificaciones(): void {
    this.mostrarBannerNotif = false;
    localStorage.setItem('webpush_suscrito', 'rechazado');
  }

  private mostrarNotificacion(msg: string): void {
    this.notificacion = msg;
    this.error = null;
    setTimeout(() => (this.notificacion = null), 3500);
  }

  private mostrarError(msg: string): void {
    this.error = msg;
    this.notificacion = null;
    setTimeout(() => (this.error = null), 4000);
  }
}
