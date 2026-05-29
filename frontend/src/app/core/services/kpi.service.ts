import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment.development';

// ── Interfaces que representan la respuesta de cada endpoint KPI ──────────────

export interface KpiResumen {
  total_asignaciones: number;
  completadas: number;
  canceladas: number;
  rechazadas: number;
  en_progreso: number;
  disponibles_sin_atender: number;
  ingresos_totales: number;
  comisiones_generadas: number;
  calificacion_promedio: number | null;
}

export interface KpiPorTipo {
  categoria: string;
  total: number;
  porcentaje: number;
}

export interface KpiPorFecha {
  fecha: string;
  total: number;
}

export interface KpiTiempos {
  tiempo_asignacion_min: number | null;
  tiempo_llegada_min: number | null;
  tiempo_servicio_min: number | null;
  tiempo_total_min: number | null;
  total_servicios_medidos: number;
  nota?: string;
}

export interface KpiTaller {
  taller_id: number;
  taller: string;
  servicios_completados: number;
  servicios_cancelados: number;
  calificacion_promedio: number | null;
  ingresos_totales: number;
  tiempo_respuesta_min: number | null;
}

export interface KpiZona {
  lat: number;
  lng: number;
  total: number;
}

export interface KpiSla {
  total_completados: number;
  dentro_sla: number;
  fuera_sla: number;
  porcentaje_sla: number;
  limite_horas: number;
}

// ── Filtros opcionales que todos los endpoints aceptan ───────────────────────

export interface KpiFiltros {
  fecha_desde?: string;  // formato ISO: '2026-01-01T00:00:00'
  fecha_hasta?: string;
  taller_id?: number;
  agrupacion?: 'dia' | 'semana' | 'mes';
  precision?: number;
  limite_horas?: number;
}

// ─────────────────────────────────────────────────────────────────────────────

@Injectable({ providedIn: 'root' })
export class KpiService {
  private http = inject(HttpClient);
  private readonly API_URL = environment.apiUrl;

  /**
   * Convierte los filtros a HttpParams.
   * Solo agrega los parámetros que no sean undefined/null.
   */
  private buildParams(filtros?: KpiFiltros): HttpParams {
    let params = new HttpParams();
    if (!filtros) return params;

    if (filtros.fecha_desde) params = params.set('fecha_desde', filtros.fecha_desde);
    if (filtros.fecha_hasta) params = params.set('fecha_hasta', filtros.fecha_hasta);
    if (filtros.taller_id)   params = params.set('taller_id',   filtros.taller_id.toString());
    if (filtros.agrupacion)  params = params.set('agrupacion',  filtros.agrupacion);
    if (filtros.precision !== undefined) params = params.set('precision', filtros.precision.toString());
    if (filtros.limite_horas !== undefined) params = params.set('limite_horas', filtros.limite_horas.toString());

    return params;
  }

  getResumen(filtros?: KpiFiltros): Observable<KpiResumen> {
    return this.http.get<KpiResumen>(`${this.API_URL}/kpi/resumen`, {
      params: this.buildParams(filtros)
    });
  }

  getPorTipo(filtros?: KpiFiltros): Observable<KpiPorTipo[]> {
    return this.http.get<KpiPorTipo[]>(`${this.API_URL}/kpi/incidentes-por-tipo`, {
      params: this.buildParams(filtros)
    });
  }

  getPorFecha(filtros?: KpiFiltros): Observable<KpiPorFecha[]> {
    return this.http.get<KpiPorFecha[]>(`${this.API_URL}/kpi/incidentes-por-fecha`, {
      params: this.buildParams(filtros)
    });
  }

  getTiempos(filtros?: KpiFiltros): Observable<KpiTiempos> {
    return this.http.get<KpiTiempos>(`${this.API_URL}/kpi/tiempos-promedio`, {
      params: this.buildParams(filtros)
    });
  }

  getRankingTalleres(filtros?: KpiFiltros): Observable<KpiTaller[]> {
    return this.http.get<KpiTaller[]>(`${this.API_URL}/kpi/ranking-talleres`, {
      params: this.buildParams(filtros)
    });
  }

  getZonas(filtros?: KpiFiltros): Observable<KpiZona[]> {
    return this.http.get<KpiZona[]>(`${this.API_URL}/kpi/zonas-incidentes`, {
      params: this.buildParams(filtros)
    });
  }

  getSla(filtros?: KpiFiltros): Observable<KpiSla> {
    return this.http.get<KpiSla>(`${this.API_URL}/kpi/sla`, {
      params: this.buildParams(filtros)
    });
  }
}
