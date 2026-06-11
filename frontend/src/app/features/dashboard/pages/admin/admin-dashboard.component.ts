import {
  Component, OnInit, OnDestroy, AfterViewInit,
  ViewChild, ElementRef, inject, ChangeDetectorRef
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { Chart, registerables } from 'chart.js';

// Importar Leaflet solo en el navegador (no durante SSR)
import * as L from 'leaflet';

import {
  KpiService,
  KpiResumen, KpiPorTipo, KpiPorFecha,
  KpiTiempos, KpiTaller, KpiSla
} from '../../../../core/services/kpi.service';

// Registrar todos los módulos de Chart.js (scales, charts, plugins, etc.)
Chart.register(...registerables);

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './admin-dashboard.component.html',
  styleUrl: './admin-dashboard.component.css'
})
export class AdminDashboardComponent implements OnInit, AfterViewInit, OnDestroy {

  // ── Inyección de dependencias ──────────────────────────────
  private kpiService = inject(KpiService);
  private cdr        = inject(ChangeDetectorRef);

  // ── Referencias a los canvas para Chart.js ─────────────────
  @ViewChild('canvasTipos',   { static: false }) canvasTipos!:   ElementRef<HTMLCanvasElement>;
  @ViewChild('canvasFechas',  { static: false }) canvasFechas!:  ElementRef<HTMLCanvasElement>;
  @ViewChild('contenedorMapa', { static: false }) contenedorMapa!: ElementRef<HTMLDivElement>;

  // ── Instancias de gráficos (para destruirlos en ngOnDestroy) ─
  private chartTipos?:  Chart;
  private chartFechas?: Chart;
  private mapa?:        L.Map;

  // ── Fecha actual para el header ────────────────────────────
  today = new Date();

  // ── Estado de carga ────────────────────────────────────────
  loading    = true;
  error      = false;

  // ── Datos cargados desde la API ───────────────────────────
  resumen?:   KpiResumen;
  tiempos?:   KpiTiempos;
  talleres:   KpiTaller[]  = [];
  sla?:       KpiSla;
  porTipo:    KpiPorTipo[] = [];
  porFecha:   KpiPorFecha[] = [];

  // ── Indicador: si los gráficos ya se dibujaron ─────────────
  private chartsListos = false;

  // ── Filtros de fecha ───────────────────────────────────────
  fechaDesde = '';
  fechaHasta = '';
  agrupacion: 'dia' | 'semana' | 'mes' = 'mes';

  // ─────────────────────────────────────────────────────────────
  // CICLO DE VIDA
  // ─────────────────────────────────────────────────────────────

  ngOnInit(): void {
    this.cargarTodo();
  }

  /**
   * ngAfterViewInit se ejecuta DESPUÉS de que el DOM (con los <canvas>)
   * está disponible. Si los datos ya cargaron antes (muy improbable),
   * dibujamos los gráficos aquí. Normalmente los dibuja cargarTodo().
   */
  ngAfterViewInit(): void {
    this.chartsListos = true;
    // Si los datos ya llegaron antes de que el DOM esté listo, dibujar ahora
    if (this.porTipo.length > 0)  this.dibujarChartTipos();
    if (this.porFecha.length > 0) this.dibujarChartFechas();
  }

  ngOnDestroy(): void {
    // Destruir los gráficos para liberar memoria
    this.chartTipos?.destroy();
    this.chartFechas?.destroy();
    this.mapa?.remove();
  }

  // ─────────────────────────────────────────────────────────────
  // CARGA DE DATOS
  // ─────────────────────────────────────────────────────────────

  cargarTodo(): void {
    this.loading = true;
    this.error   = false;

    // Construir filtros solo si el usuario los llenó
    const filtros = this.buildFiltros();

    forkJoin({
      resumen:  this.kpiService.getResumen(filtros),
      tipos:    this.kpiService.getPorTipo(filtros),
      fechas:   this.kpiService.getPorFecha({ ...filtros, agrupacion: this.agrupacion }),
      tiempos:  this.kpiService.getTiempos(filtros),
      talleres: this.kpiService.getRankingTalleres(filtros),
      sla:      this.kpiService.getSla(filtros),
      zonas:    this.kpiService.getZonas({ ...filtros, precision: 1 }),
    }).subscribe({
      next: (data) => {
        this.resumen  = data.resumen;
        this.porTipo  = data.tipos;
        this.porFecha = data.fechas;
        this.tiempos  = data.tiempos;
        this.talleres = data.talleres;
        this.sla      = data.sla;
        this.loading  = false;

        // Forzar detección de cambios para que Angular actualice la vista
        // antes de que intentemos acceder a los canvas
        this.cdr.detectChanges();

        // Dibujar gráficos (solo si el DOM ya está listo)
        if (this.chartsListos) {
          this.dibujarChartTipos();
          this.dibujarChartFechas();
          this.dibujarMapa(data.zonas);
        }
      },
      error: () => {
        this.loading = false;
        this.error   = true;
      }
    });
  }

  aplicarFiltros(): void {
    // Destruir gráficos previos para recrearlos con nuevos datos
    this.chartTipos?.destroy();
    this.chartFechas?.destroy();
    this.chartTipos  = undefined;
    this.chartFechas = undefined;
    this.cargarTodo();
  }

  private buildFiltros() {
    const f: Record<string, string> = {};
    if (this.fechaDesde) f['fecha_desde'] = `${this.fechaDesde}T00:00:00`;
    if (this.fechaHasta) f['fecha_hasta'] = `${this.fechaHasta}T23:59:59`;
    return Object.keys(f).length > 0 ? f : undefined;
  }

  // ─────────────────────────────────────────────────────────────
  // GRÁFICO 1 — Barras: incidentes por tipo
  // ─────────────────────────────────────────────────────────────

  private dibujarChartTipos(): void {
    if (!this.canvasTipos?.nativeElement || this.porTipo.length === 0) return;

    // Si ya existe un gráfico en este canvas, destruirlo primero
    this.chartTipos?.destroy();

    const labels  = this.porTipo.map(d => d.categoria);
    const valores = this.porTipo.map(d => d.total);
    const colores = [
      '#3B82F6', '#F87171', '#10B981',
      '#FBBF24', '#A78BFA', '#F97316',
      '#06B6D4', '#EC4899'
    ];

    this.chartTipos = new Chart(this.canvasTipos.nativeElement, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Incidentes',
          data: valores,
          backgroundColor: colores.slice(0, labels.length),
          borderRadius: 8,
          borderSkipped: false,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.parsed.y} incidentes (${this.porTipo[ctx.dataIndex]?.porcentaje}%)`
            }
          }
        },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, grid: { color: '#F1F5F9' } }
        }
      }
    });
  }

  // ─────────────────────────────────────────────────────────────
  // GRÁFICO 2 — Línea: incidentes por fecha
  // ─────────────────────────────────────────────────────────────

  private dibujarChartFechas(): void {
    if (!this.canvasFechas?.nativeElement || this.porFecha.length === 0) return;

    this.chartFechas?.destroy();

    const labels  = this.porFecha.map(d => d.fecha);
    const valores = this.porFecha.map(d => d.total);

    this.chartFechas = new Chart(this.canvasFechas.nativeElement, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Incidentes',
          data: valores,
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59,130,246,0.08)',
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#3B82F6',
          pointRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, grid: { color: '#F1F5F9' } }
        }
      }
    });
  }

  // ─────────────────────────────────────────────────────────────
  // MAPA — Leaflet: zonas con más incidentes
  // ─────────────────────────────────────────────────────────────

  private dibujarMapa(zonas: { lat: number; lng: number; total: number }[]): void {
    if (!this.contenedorMapa?.nativeElement) return;

    // Si ya hay un mapa, quitarlo primero
    this.mapa?.remove();

    // Calcular el centro del mapa (promedio de las zonas, o Santa Cruz por defecto)
    const centroLat = zonas.length > 0
      ? zonas.reduce((s, z) => s + z.lat, 0) / zonas.length
      : -17.7833;
    const centroLng = zonas.length > 0
      ? zonas.reduce((s, z) => s + z.lng, 0) / zonas.length
      : -63.1812;

    this.mapa = L.map(this.contenedorMapa.nativeElement, {
      center: [centroLat, centroLng],
      zoom: 12,
      zoomControl: true,
    });

    // Capa base: OpenStreetMap (gratuita, sin API key)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18,
    }).addTo(this.mapa);

    if (zonas.length === 0) return;

    // Calcular el total máximo para escalar los círculos proporcionalmente
    const maxTotal = Math.max(...zonas.map(z => z.total));

    zonas.forEach(zona => {
      // Radio proporcional al total: entre 10px y 50px
      const radio = 10 + (zona.total / maxTotal) * 40;

      // Intensidad del color: más rojo = más incidentes
      const intensidad = Math.round((zona.total / maxTotal) * 255);
      const color = `rgba(${intensidad}, ${60}, ${80}, 0.6)`;

      L.circle([zona.lat, zona.lng], {
        radius: radio * 80,   // en metros (el mapa lo escala según el zoom)
        color:       color,
        fillColor:   color,
        fillOpacity: 0.6,
        weight: 1,
      })
        .addTo(this.mapa!)
        .bindPopup(`<b>${zona.total} incidentes</b><br>Lat: ${zona.lat}, Lng: ${zona.lng}`);
    });
  }

  // ─────────────────────────────────────────────────────────────
  // HELPERS PARA LA VISTA
  // ─────────────────────────────────────────────────────────────

  get porcentajeCancelacion(): number {
    if (!this.resumen || this.resumen.total_asignaciones === 0) return 0;
    return Math.round(this.resumen.canceladas * 100 / this.resumen.total_asignaciones);
  }

  get slaColor(): string {
    if (!this.sla) return 'bg-gray-200';
    if (this.sla.porcentaje_sla >= 80) return 'bg-green-500';
    if (this.sla.porcentaje_sla >= 50) return 'bg-yellow-400';
    return 'bg-red-500';
  }

  trackByTaller(_: number, t: KpiTaller): number {
    return t.taller_id;
  }

  calcularBarra(minutos: number | null | undefined): number {
    if (!minutos) return 0;
    return Math.min(Math.round(minutos / 120 * 100), 100);
  }
}
