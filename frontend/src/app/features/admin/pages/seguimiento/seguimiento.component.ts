/**
 * seguimiento.component.ts
 *
 * Pantalla de seguimiento en tiempo real para el administrador del taller.
 *
 * Funcionalidad:
 *  1. Lista asignaciones activas (estado en_camino, en_atencion)
 *  2. Al seleccionar una: conecta al WebSocket e inicializa mapa Leaflet
 *  3. Al recibir "ubicacion_mecanico": mueve el marcador del mecánico en el mapa
 *  4. Al recibir "cambio_estado": actualiza el badge de estado
 *  5. Al destruirse el componente: cierra la conexión WebSocket
 */
import { CommonModule } from '@angular/common';
import {
  Component,
  OnInit,
  OnDestroy,
  AfterViewInit,
  inject
} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subscription } from 'rxjs';
import * as L from 'leaflet';
import { WebSocketService } from '../../../../core/services/websocket.service';
import { environment } from '../../../../../environments/environment.development';
import { AdminOpsService } from '../../../../core/services/admin-ops.service';
import { Evidencia_Item } from '../../../../core/models/admin-ops.model';



// ── Corrección del ícono de Leaflet con webpack ──────────────────────────────
// Sin esto, el marcador predeterminado de Leaflet no aparece en Angular.
// El motivo: webpack no copia los PNG del marcador automáticamente.
// Solución: usar URLs absolutas del CDN de Leaflet.
const iconoMecanico = L.icon({
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});


// Coordenadas de Cochabamba como centro por defecto del mapa
const COCHABAMBA_LAT = -17.3895;
const COCHABAMBA_LNG = -66.1540;


@Component({
  selector: 'app-seguimiento',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './seguimiento.component.html'
})
export class SeguimientoComponent implements OnInit {

  private wsService = inject(WebSocketService);
  private http = inject(HttpClient);
  private adminOpsService = inject(AdminOpsService);

  // ── Estado de la UI ───────────────────────────────────────────────────────
  asignaciones: any[] = [];
  asignacion_activa: any | null = null;
  estado_actual: string = '';          // badge de estado en tiempo real
  loading_asignaciones = false;
  error: string | null = null;

  // ── Estado de la conexión WS ──────────────────────────────────────────────
  get ws_estado(): string {
    return this.wsService.estado;
  }

  // ── Mapa Leaflet ──────────────────────────────────────────────────────────
  private mapa: L.Map | null = null;
  private marcador_mecanico: L.Marker | null = null;

  // ── Suscripción a mensajes WebSocket ──────────────────────────────────────
  private ws_sub: Subscription | null = null;

  ngOnInit(): void {
    this.cargarAsignaciones();
  }

  ngOnDestroy(): void {
    // Importante: liberar recursos al destruir el componente
    this.wsService.desconectar();
    this.ws_sub?.unsubscribe();
    this.destruirMapa();
  }


  // ── Carga de datos
  cargarAsignaciones(): void {
    this.loading_asignaciones = true;
    this.http
      .get<any[]>(`${environment.apiUrl}/asignaciones/`)
      .subscribe({
        next: (data) => {
          const listado = Array.isArray(data) ? data : [];
          // Solo mostrar las asignaciones activas (en camino o en atención)
          this.asignaciones = listado.filter((a) =>
            ['en_camino', 'en_atencion'].includes(String(a?.estado || ''))
          );
          this.loading_asignaciones = false;
        },
        error: () => {
          this.error = 'No se pudieron cargar las asignaciones activas.';
          this.loading_asignaciones = false;
        },
      });
  }

  // cargarAsignacionesEnProceso(): void {
  //   this.loading_asignaciones = true;
  //   this.adminOpsService.getAsignaciones().subscribe({
  //     next: (data) => {
  //       const listado = Array.isArray(data) ? data : [];
  //       this.asignaciones_en_proceso = listado.filter(
  //         (asignacion) => String(asignacion?.estado || '').toLowerCase() === 'en proceso'
  //       );
  //       this.loading_asignaciones = false;
  //     },
  //     error: () => {
  //       this.error = 'No se pudieron cargar las asignaciones en proceso.';
  //       this.loading_asignaciones = false;
  //     }
  //   });
  // }

  // ── Selección de asignación ───────────────────────────────────────────────

  seleccionarAsignacion(asignacion: any): void {
    // Si ya estaba seleccionada, no hacer nada
    if (this.asignacion_activa?.id === asignacion.id) return;

    // Limpiar estado anterior
    this.wsService.desconectar();
    this.ws_sub?.unsubscribe();
    this.destruirMapa();

    // Activar la nueva asignación
    this.asignacion_activa = asignacion;
    this.estado_actual = asignacion.estado || '';
    this.error = null;

    const incidente_id: number = Number(
      asignacion.incidente_id ?? asignacion.incidente?.id
    );

    if (!incidente_id) {
      this.error = 'Esta asignación no tiene incidente asociado.';
      return;
    }

    // 1. Inicializar el mapa (setTimeout para esperar que Angular renderice el div)
    setTimeout(() => {
      this.inicializarMapa();

      // 2. Intentar obtener la última posición conocida del mecánico
      //    (para mostrar el marcador de inmediato sin esperar el próximo ping)
      this.http
        .get<any>(`${environment.apiUrl}/ws/posicion/${incidente_id}`)
        .subscribe({
          next: (res) => {
            if (res?.posicion?.lat && res?.posicion?.lng) {
              this.actualizarMarcador(res.posicion.lat, res.posicion.lng);
            }
          },
          error: () => {
            // 404 = mecánico aún no envió posición — normal, no es un error real
            console.log('[Seguimiento] Mecánico aún no envió posición inicial.');
          },
        });

      // 3. Conectar al WebSocket
      this.wsService.conectar(incidente_id, 'cliente');

      // 4. Escuchar mensajes del WebSocket
      this.ws_sub = this.wsService.mensajes$.subscribe((msg) => {
        this.manejarMensajeWS(msg);
      });
    }, 0);
  }

  // ── Manejo de mensajes WebSocket ──────────────────────────────────────────

  private manejarMensajeWS(msg: any): void {
    console.log('[Seguimiento] Mensaje WS recibido:', msg);

    switch (msg.tipo) {
      case 'ubicacion_mecanico':
        // El mecánico envió su posición GPS → mover marcador
        if (msg.lat != null && msg.lng != null) {
          this.actualizarMarcador(msg.lat, msg.lng);
        }
        break;

      case 'cambio_estado':
        // El mecánico cambió el estado → actualizar badge
        if (msg.estado) {
          this.estado_actual = msg.estado;
          if (this.asignacion_activa) {
            this.asignacion_activa = {
              ...this.asignacion_activa,
              estado: msg.estado,
            };
          }
          // Si finalizó o canceló, desconectar el WS
          if (['finalizado', 'cancelado'].includes(msg.estado)) {
            this.wsService.desconectar();
          }
        }
        break;

      case 'conexion_exitosa':
        console.log('[Seguimiento] Conectado al WS. Clientes en el canal:', msg.conectados);
        // Si el servidor envía la última posición en el mensaje de bienvenida, usarla
        if (msg.ultima_posicion_mecanico?.lat) {
          this.actualizarMarcador(
            msg.ultima_posicion_mecanico.lat,
            msg.ultima_posicion_mecanico.lng
          );
        }
        break;

      default:
        break;
    }
  }

  // ── Mapa Leaflet ──────────────────────────────────────────────────────────

  private inicializarMapa(): void {
    const contenedor = document.getElementById('mapa-seguimiento');
    if (!contenedor) {
      console.error('[Seguimiento] No se encontró el div #mapa-seguimiento');
      return;
    }

    // Destruir mapa anterior si existe (evita error "Map container is already initialized")
    this.destruirMapa();

    this.mapa = L.map('mapa-seguimiento', {
      center: [COCHABAMBA_LAT, COCHABAMBA_LNG],
      zoom: 14,
    });

    // Capa base de OpenStreetMap (gratuita, no requiere API key)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(this.mapa);

    console.log('[Seguimiento] Mapa inicializado.');
  }

  private actualizarMarcador(lat: number, lng: number): void {
    if (!this.mapa) return;

    const posicion = L.latLng(lat, lng);

    if (!this.marcador_mecanico) {
      // Primera vez: crear el marcador
      this.marcador_mecanico = L.marker(posicion, { icon: iconoMecanico })
        .addTo(this.mapa)
        .bindPopup('🔧 Mecánico en camino');
    } else {
      // Ya existe: solo mover
      this.marcador_mecanico.setLatLng(posicion);
    }

    // Centrar el mapa en la nueva posición del mecánico
    this.mapa.setView(posicion, this.mapa.getZoom());
  }

  private destruirMapa(): void {
    if (this.marcador_mecanico) {
      this.marcador_mecanico.remove();
      this.marcador_mecanico = null;
    }
    if (this.mapa) {
      this.mapa.remove();
      this.mapa = null;
    }
  }

  // ── Helpers de UI ─────────────────────────────────────────────────────────

  getColorEstado(estado: string): string {
    const colores: Record<string, string> = {
      en_camino:       'bg-blue-100 text-blue-800',
      en_atencion:     'bg-yellow-100 text-yellow-800',
      finalizado:      'bg-green-100 text-green-800',
      cancelado:       'bg-red-100 text-red-800',
      taller_asignado: 'bg-purple-100 text-purple-800',
    };
    return colores[estado] ?? 'bg-gray-100 text-gray-800';
  }

  getEtiquetaEstado(estado: string): string {
    const etiquetas: Record<string, string> = {
      en_camino:       'En camino',
      en_atencion:     'En atención',
      finalizado:      'Finalizado',
      cancelado:       'Cancelado',
      taller_asignado: 'Taller asignado',
    };
    return etiquetas[estado] ?? estado;
  }

  getColorWS(): string {
    const colores: Record<string, string> = {
      conectado:   'bg-green-500',
      conectando:  'bg-yellow-500',
      error:       'bg-red-500',
      desconectado:'bg-gray-400',
    };
    return colores[this.ws_estado] ?? 'bg-gray-400';
  }

  // getEvidenciaUrl(item: Evidencia_Item): string {
  //   return item.url || item.archivo_url || item.imagen_url || item.foto_url || '';
  // }
}
