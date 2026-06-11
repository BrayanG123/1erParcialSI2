import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IncidenteService } from '../../../../core/services/incidente.service';
import { MecanicoService } from '../../../../core/services/mecanico.service';
import { AsignacionService } from '../../../../core/services/asignacion.service';
import { AsignacionRequest } from '../../../../core/models/asignacion.model';

import { WebPushService } from '../../../../core/services/web-push.service';


@Component({
  selector: 'app-incidentes-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './incidentes-list.component.html'
})
export class IncidentesListComponent implements OnInit {
  private incidenteService = inject(IncidenteService);
  private mecanicoService = inject(MecanicoService);
  private asignacionService = inject(AsignacionService);
  private webPushService = inject(WebPushService);


  // Estado del banner de notificaciones
  mostrarBannerNotif = !this.webPushService.yaSuscrito && this.webPushService.estaDisponible;

  // Pestañas
  tabActiva: 'pendientes' | 'historial' = 'pendientes';

  // Datos
  incidentesPendientes: any[] = [];
  incidentesHistorial: any[] = [];
  mecanicos: any[] = [];

  // UI
  loading = false;
  notificacion: string | null = null;
  error: string | null = null;

  // Filtros
  filtroPrioridad = '';
  filtroDistancia = '50';
  searchTerm = '';

  // Orden y paginación (cliente)
  ordenRecientes = true;
  pagina = 1;
  tamanoPagina = 10;
  probandoPushId: number | null = null;
  Math = Math; // para usar Math.min en el template

  ngOnInit(): void {
    this.cargarDatos();
  }

  cambiarTab(tab: 'pendientes' | 'historial') {
    this.tabActiva = tab;
  }

  activarNotificaciones(): void {
    this.webPushService.suscribir().subscribe({
      complete: () => {
        this.mostrarBannerNotif = false;
      }
    });
  }

  rechazarNotificaciones(): void {
    this.mostrarBannerNotif = false;
    localStorage.setItem('webpush_suscrito', 'rechazado');
  }

  cargarDatos() {
    this.loading = true;

    // Incidentes disponibles (sin asignar)
    this.incidenteService.getIncidentesDisponibles().subscribe({
      next: (data) => {
        this.incidentesPendientes = Array.isArray(data) ? data.map(inc => ({
          ...inc,
          distancia: (Math.random() * 10 + 1).toFixed(1) + ' km', // Dato estático como pidió el usuario
          tiempo: `Hace ${Math.floor(Math.random() * 30 + 5)} min`, // Dato estático
          prioridad: this.determinarPrioridad(inc)
        })) : [];
        this.loading = false;
      },
      error: () => {
        this.incidentesPendientes = [];
        this.loading = false;
      }
    });

    // Historial — incidentes ya asignados al taller
    this.incidenteService.getIncidentes().subscribe({
      next: (data) => {
        this.incidentesHistorial = Array.isArray(data) ? data : [];
      },
      error: () => {
        this.incidentesHistorial = [];
      }
    });

    // Mecánicos del taller
    this.mecanicoService.getMecanicos().subscribe({
      next: (data) => this.mecanicos = Array.isArray(data) ? data : [],
      error: () => this.mecanicos = []
    });
  }

  asignarMecanico(incidenteId: number, event: any) {
    const mecanicoId = event?.target?.value;
    if (!mecanicoId) return;

    const datos: AsignacionRequest = {
      incidente_id: incidenteId,
      mecanico_id: parseInt(mecanicoId),
      notas: 'Asignación desde panel administrador'
    };

    this.asignacionService.crearAsignacion(datos).subscribe({
      next: () => {
        // Quitar de pendientes y recargar historial
        this.incidentesPendientes = this.incidentesPendientes.filter(i => i.id !== incidenteId);
        this.incidenteService.getIncidentes().subscribe({
          next: (data) => this.incidentesHistorial = Array.isArray(data) ? data : []
        });
        this.mostrarNotificacion('Mecánico asignado con éxito');
      },
      error: (err) => {
        this.mostrarError(err?.error?.detail || 'No se pudo completar la asignación');
      }
    });
  }

  private determinarPrioridad(inc: any): 'Alta' | 'Media' | 'Baja' {
    const desc = (inc.descripcion || '').toLowerCase();
    const cat = (inc.categoria?.nombre || '').toLowerCase();

    if (desc.includes('choque') || desc.includes('accidente') || desc.includes('fuego') || cat.includes('emergencia')) {
      return 'Alta';
    }
    if (desc.includes('motor') || desc.includes('frenos') || desc.includes('arranca')) {
      return 'Media';
    }
    return 'Baja';
  }

  getPrioridadBadgeClass(prioridad: string): string {
    switch (prioridad) {
      case 'Alta': return 'bg-red-50 text-red-600';
      case 'Media': return 'bg-orange-50 text-orange-600';
      case 'Baja': return 'bg-emerald-50 text-emerald-600';
      default: return 'bg-gray-50 text-gray-600';
    }
  }

  getFilteredIncidentes() {
    const factor = this.ordenRecientes ? -1 : 1;
    return this.incidentesPendientes
      .filter(inc => {
        const matchSearch = !this.searchTerm ||
          inc.descripcion.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
          inc.id.toString().includes(this.searchTerm);

        const matchPrioridad = !this.filtroPrioridad || inc.prioridad === this.filtroPrioridad;

        const distanciaNum = parseFloat(inc.distancia);
        const matchDistancia = this.filtroDistancia === '50' || distanciaNum <= parseInt(this.filtroDistancia);

        return matchSearch && matchPrioridad && matchDistancia;
      })
      .sort((a, b) =>
        factor * (new Date(a.fecha_hora ?? 0).getTime() - new Date(b.fecha_hora ?? 0).getTime())
      );
  }

  // ── Paginación ──────────────────────────────────────────────

  getIncidentesPagina() {
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
          this.mostrarError('❌ ' + (diag.conclusion ?? diag.error ?? 'Falló el envío. Ver consola (F12).'));
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

  /**
   * Acepta un incidente de la lista de solicitudes disponibles
   * @param incidenteId ID del incidente a aceptar
   */
  aceptarIncidente(incidenteId: number) {
    this.loading = true;
    // Se envía el ID del incidente. Como mecanico_id no se provee, el backend
    // crea una asignación en estado 'pendiente' vinculada a tu taller (tenant).
    const datos: AsignacionRequest = {
      incidente_id: incidenteId
    };
    this.asignacionService.crearAsignacion(datos).subscribe({
      next: () => {
        // Remover el incidente de la lista local
        this.incidentesPendientes = this.incidentesPendientes.filter(i => i.id !== incidenteId);
        this.loading = false;
        this.mostrarNotificacion('¡Solicitud aceptada! Ahora puedes asignarle un mecánico en la sección de Asignaciones.');
      },
      error: (err) => {
        this.loading = false;
        this.mostrarError(err?.error?.detail || 'No se pudo aceptar la solicitud');
      }
    });
  }

  rechazarIncidente(id: number) {
    if (confirm('¿Estás seguro de rechazar esta solicitud?')) {
      this.incidentesPendientes = this.incidentesPendientes.filter(i => i.id !== id);
      this.mostrarNotificacion('Solicitud rechazada');
    }
  }

  verDetalle(inc: any) {
    // Por ahora solo mostrar un alert o log, ya que no hay ruta de detalle especificada
    alert(`Detalle del Incidente #${inc.id}\nDescripción: ${inc.descripcion}\nUbicación: ${inc.latitud}, ${inc.longitud}`);
  }

  private mostrarNotificacion(msg: string) {
    this.notificacion = msg;
    this.error = null;
    setTimeout(() => this.notificacion = null, 3000);
  }

  private mostrarError(msg: string) {
    this.error = msg;
    this.notificacion = null;
    setTimeout(() => this.error = null, 4000);
  }
}
