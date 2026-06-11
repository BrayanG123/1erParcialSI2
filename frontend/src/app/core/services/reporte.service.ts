import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment.development';

// ── Contrato QBE (espejo de backend/app/schemas/reporte_qbe.py) ──

export interface FiltroQBE {
  campo: string;
  operador: string;
  valor?: any;
}

export interface AgregacionQBE {
  funcion: string;          // contar | sumar | promedio | minimo | maximo
  campo?: string | null;
  alias?: string | null;
}

export interface QBERequest {
  entidad: string;
  filtros?: FiltroQBE[];
  rango_fechas?: { campo?: string | null; desde?: string | null; hasta?: string | null } | null;
  group_by?: string[];
  agregaciones?: AgregacionQBE[];
  orden?: { campo: string; direccion: 'asc' | 'desc' } | null;
  pagina?: number;
  tamano_pagina?: number;
}

export interface QBEResponse {
  entidad: string;
  tipo_reporte: 'detalle' | 'agrupado';
  total: number;
  pagina: number;
  tamano_pagina: number;
  columnas: string[];
  filas: Record<string, any>[];
}

export interface EsquemaQBE {
  entidades: Record<string, { campos: string[]; fecha_defecto: string | null }>;
  operadores: string[];
  agregaciones: string[];
  limites: { tamano_pagina_max: number };
}

@Injectable({ providedIn: 'root' })
export class ReporteService {
  private http = inject(HttpClient);
  private readonly API_URL = `${environment.apiUrl}/reportes`;

  // Catálogo de entidades/campos/operadores (también alimentará al LLM en Fase 3)
  getEsquema() {
    return this.http.get<EsquemaQBE>(`${this.API_URL}/qbe/esquema`);
  }

  // Ejecuta un reporte dinámico QBE
  generarReporte(qbe: QBERequest) {
    return this.http.post<QBEResponse>(`${this.API_URL}/qbe`, qbe);
  }
}
