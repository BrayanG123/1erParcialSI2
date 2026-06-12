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

  // ── IA: lenguaje natural → QBE → reporte ──

  // Envía el prompt del usuario; el backend lo traduce a QBE con el LLM,
  // lo ejecuta y devuelve el QBE generado + el resultado
  generarDesdeTexto(texto: string) {
    return this.http.post<{
      prompt: string;
      modelo_usado: string;
      qbe_generado: QBERequest;
      auto_corregido: boolean;
      resultado: QBEResponse;
    }>(`${this.API_URL}/desde-texto`, { texto });
  }

  // Convierte audio del micrófono a texto (Azure Speech-to-Text del backend)
  transcribirAudio(audio: Blob) {
    const formData = new FormData();
    formData.append('archivo', audio, 'grabacion.webm');
    return this.http.post<{ texto: string }>(`${this.API_URL}/transcribir-audio`, formData);
  }

  // ── Exportación y envío por correo ──

  // Descarga el reporte como archivo (Excel o PDF) generado en el backend.
  // responseType 'blob' = la respuesta es un archivo binario, no JSON
  exportarReporte(qbe: QBERequest, formato: 'excel' | 'pdf') {
    return this.http.post(`${this.API_URL}/exportar?formato=${formato}`, qbe, {
      responseType: 'blob',
      observe: 'response',   // para leer el nombre del archivo del header
    });
  }

  // Genera el reporte en el backend y lo envía por email como adjunto
  enviarPorCorreo(qbe: QBERequest, destinatario: string, formato: 'excel' | 'pdf', mensaje?: string) {
    return this.http.post<{
      enviado: boolean;
      destinatario: string;
      archivo: string;
      total_registros: number;
    }>(`${this.API_URL}/enviar-correo`, { qbe, destinatario, formato, mensaje: mensaje || null });
  }
}
