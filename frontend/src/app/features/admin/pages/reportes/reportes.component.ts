import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ReporteService, EsquemaQBE, QBERequest, QBEResponse, FiltroQBE, AgregacionQBE
} from '../../../../core/services/reporte.service';

// Filtro editable en la UI (el valor siempre se edita como texto y se castea al enviar)
interface FiltroUI { campo: string; operador: string; valor: string; }
interface AgregacionUI { funcion: string; campo: string; alias: string; }

// Operadores que no necesitan valor
const SIN_VALOR = ['es_nulo', 'no_es_nulo'];

@Component({
  selector: 'app-reportes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './reportes.component.html'
})
export class ReportesComponent implements OnInit {
  private reporteService = inject(ReporteService);

  // Esquema cargado del backend
  esquema: EsquemaQBE | null = null;
  entidades: string[] = [];

  // ── Estado del constructor de consultas ──
  entidad = '';
  tipoReporte: 'gerencial' | 'ejecutivo' = 'gerencial';
  filtros: FiltroUI[] = [];
  fechaDesde = '';
  fechaHasta = '';
  campoFecha = '';            // vacío = usar el por defecto de la entidad
  groupBy: string[] = [];
  agregaciones: AgregacionUI[] = [];
  ordenCampo = '';
  ordenDireccion: 'asc' | 'desc' = 'desc';
  pagina = 1;
  tamanoPagina = 50;

  // ── Resultado ──
  resultado: QBEResponse | null = null;
  loading = false;
  error: string | null = null;

  // ── IA: prompt por texto o voz ──
  prompt = '';
  generandoIA = false;
  modeloUsado: string | null = null;     // se muestra tras generar con IA
  grabando = false;
  transcribiendo = false;
  private mediaRecorder: MediaRecorder | null = null;
  private chunksAudio: Blob[] = [];

  // ── Exportación y envío por correo ──
  exportando: 'excel' | 'pdf' | null = null;
  mostrarPanelCorreo = false;
  correoDestino = '';
  correoFormato: 'excel' | 'pdf' = 'excel';
  correoMensaje = '';
  enviandoCorreo = false;
  correoExito: string | null = null;

  ngOnInit(): void {
    this.reporteService.getEsquema().subscribe({
      next: (e) => {
        this.esquema = e;
        this.entidades = Object.keys(e.entidades).sort();
      },
      error: () => (this.error = 'No se pudo cargar el esquema de reportes.')
    });
  }

  // ── Helpers de la UI ──

  get camposEntidad(): string[] {
    return this.esquema?.entidades[this.entidad]?.campos ?? [];
  }

  get operadores(): string[] {
    return this.esquema?.operadores ?? [];
  }

  get funcionesAgregacion(): string[] {
    return this.esquema?.agregaciones ?? [];
  }

  requiereValor(operador: string): boolean {
    return !SIN_VALOR.includes(operador);
  }

  onEntidadChange(): void {
    // Al cambiar de entidad, los campos viejos ya no aplican
    this.filtros = [];
    this.groupBy = [];
    this.agregaciones = [];
    this.ordenCampo = '';
    this.campoFecha = '';
    this.resultado = null;
    this.pagina = 1;
  }

  agregarFiltro(): void {
    this.filtros.push({ campo: this.camposEntidad[0] ?? '', operador: 'igual', valor: '' });
  }

  quitarFiltro(i: number): void {
    this.filtros.splice(i, 1);
  }

  agregarAgregacion(): void {
    this.agregaciones.push({ funcion: 'contar', campo: '', alias: '' });
  }

  quitarAgregacion(i: number): void {
    this.agregaciones.splice(i, 1);
  }

  toggleGroupBy(campo: string): void {
    const idx = this.groupBy.indexOf(campo);
    idx >= 0 ? this.groupBy.splice(idx, 1) : this.groupBy.push(campo);
  }

  // Campos ordenables: los de la entidad + los alias de agregaciones (en ejecutivo)
  get camposOrdenables(): string[] {
    if (this.tipoReporte === 'ejecutivo') {
      const aliases = this.agregaciones
        .map(a => a.alias || `${a.funcion}_${a.campo || 'registros'}`)
        .filter(Boolean);
      return [...this.groupBy, ...aliases];
    }
    return this.camposEntidad;
  }

  // Castea el texto del input al tipo más probable (el backend espera tipos correctos)
  private parsearValor(texto: string, operador: string): any {
    if (operador === 'en_lista') {
      return texto.split(',').map(v => this.castear(v.trim()));
    }
    return this.castear(texto);
  }

  private castear(v: string): any {
    if (v === 'true') return true;
    if (v === 'false') return false;
    if (v !== '' && !isNaN(Number(v))) return Number(v);
    return v;
  }

  // ── Construir el QBE y ejecutar ──

  private construirQBE(): QBERequest {
    const filtros: FiltroQBE[] = this.filtros
      .filter(f => f.campo && f.operador)
      .map(f => ({
        campo: f.campo,
        operador: f.operador,
        valor: this.requiereValor(f.operador) ? this.parsearValor(f.valor, f.operador) : null,
      }));

    const qbe: QBERequest = {
      entidad: this.entidad,
      filtros,
      pagina: this.pagina,
      tamano_pagina: this.tamanoPagina,
    };

    if (this.fechaDesde || this.fechaHasta) {
      qbe.rango_fechas = {
        campo: this.campoFecha || null,
        desde: this.fechaDesde ? `${this.fechaDesde}T00:00:00` : null,
        hasta: this.fechaHasta ? `${this.fechaHasta}T23:59:59` : null,
      };
    }

    if (this.tipoReporte === 'ejecutivo') {
      qbe.group_by = this.groupBy;
      qbe.agregaciones = this.agregaciones.map<AgregacionQBE>(a => ({
        funcion: a.funcion,
        campo: a.campo || null,
        alias: a.alias || null,
      }));
    }

    if (this.ordenCampo) {
      qbe.orden = { campo: this.ordenCampo, direccion: this.ordenDireccion };
    }

    return qbe;
  }

  generar(resetPagina = true): void {
    if (!this.entidad) {
      this.error = 'Selecciona una entidad para el reporte.';
      return;
    }
    if (this.tipoReporte === 'ejecutivo' && this.agregaciones.length === 0) {
      this.error = 'Un reporte ejecutivo necesita al menos una agregación.';
      return;
    }
    if (resetPagina) this.pagina = 1;

    this.loading = true;
    this.error = null;

    this.reporteService.generarReporte(this.construirQBE()).subscribe({
      next: (res) => {
        this.resultado = res;
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.resultado = null;
        this.error = err?.error?.detail || 'Error al generar el reporte.';
      }
    });
  }

  // ── Paginación del resultado ──

  get totalPaginas(): number {
    if (!this.resultado) return 0;
    return Math.max(1, Math.ceil(this.resultado.total / this.tamanoPagina));
  }

  cambiarPagina(delta: number): void {
    const nueva = this.pagina + delta;
    if (nueva < 1 || nueva > this.totalPaginas) return;
    this.pagina = nueva;
    this.generar(false);
  }

  // Formatea celdas para la tabla (números con 2 decimales, fechas legibles)
  formatearCelda(valor: any): string {
    if (valor === null || valor === undefined) return '—';
    if (typeof valor === 'number' && !Number.isInteger(valor)) return valor.toFixed(2);
    if (typeof valor === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(valor)) {
      return new Date(valor).toLocaleString('es-BO', { dateStyle: 'short', timeStyle: 'short' });
    }
    return String(valor);
  }

  // ════════════════════════════════════════════════════════
  // IA — Reporte desde lenguaje natural (texto o voz)
  // ════════════════════════════════════════════════════════

  generarConIA(): void {
    const texto = this.prompt.trim();
    if (!texto) {
      this.error = 'Escribe (o dicta) qué reporte necesitas.';
      return;
    }
    this.generandoIA = true;
    this.error = null;
    this.modeloUsado = null;

    this.reporteService.generarDesdeTexto(texto).subscribe({
      next: (res) => {
        this.generandoIA = false;
        this.modeloUsado = res.modelo_usado + (res.auto_corregido ? ' (auto-corregido)' : '');
        this.resultado = res.resultado;
        this.pagina = res.resultado.pagina;
        // Pre-llenar el constructor con el QBE que generó la IA,
        // para que el usuario pueda revisarlo y ajustarlo
        this.aplicarQBE(res.qbe_generado);
      },
      error: (err) => {
        this.generandoIA = false;
        this.error = err?.error?.detail || 'La IA no pudo generar el reporte. Intenta reformular el prompt.';
      }
    });
  }

  // Copia el QBE generado por la IA a los controles del formulario
  private aplicarQBE(qbe: QBERequest): void {
    this.entidad = qbe.entidad;
    this.tipoReporte = (qbe.group_by?.length || qbe.agregaciones?.length) ? 'ejecutivo' : 'gerencial';

    this.filtros = (qbe.filtros ?? []).map(f => ({
      campo: f.campo,
      operador: f.operador,
      valor: Array.isArray(f.valor) ? f.valor.join(', ') : String(f.valor ?? ''),
    }));

    this.campoFecha = qbe.rango_fechas?.campo ?? '';
    this.fechaDesde = qbe.rango_fechas?.desde?.slice(0, 10) ?? '';
    this.fechaHasta = qbe.rango_fechas?.hasta?.slice(0, 10) ?? '';

    this.groupBy = [...(qbe.group_by ?? [])];
    this.agregaciones = (qbe.agregaciones ?? []).map(a => ({
      funcion: a.funcion,
      campo: a.campo ?? '',
      alias: a.alias ?? '',
    }));

    this.ordenCampo = qbe.orden?.campo ?? '';
    this.ordenDireccion = qbe.orden?.direccion ?? 'desc';
    this.tamanoPagina = qbe.tamano_pagina ?? 50;
  }

  // ── Micrófono (MediaRecorder → backend Azure STT) ──

  async toggleGrabacion(): Promise<void> {
    if (this.grabando) {
      this.mediaRecorder?.stop();   // dispara onstop → transcribir
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.chunksAudio = [];
      this.mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) this.chunksAudio.push(e.data);
      };
      this.mediaRecorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop());   // apagar el micrófono
        this.grabando = false;
        this.transcribirGrabacion();
      };

      this.mediaRecorder.start();
      this.grabando = true;
      this.error = null;
    } catch {
      this.error = 'No se pudo acceder al micrófono. Verifica los permisos del navegador.';
    }
  }

  private transcribirGrabacion(): void {
    const audio = new Blob(this.chunksAudio, { type: 'audio/webm' });
    if (audio.size === 0) return;

    this.transcribiendo = true;
    this.reporteService.transcribirAudio(audio).subscribe({
      next: (res) => {
        this.transcribiendo = false;
        // Añadir al prompt (por si el usuario ya escribió algo)
        this.prompt = this.prompt ? `${this.prompt} ${res.texto}` : res.texto;
      },
      error: (err) => {
        this.transcribiendo = false;
        this.error = err?.error?.detail || 'No se pudo transcribir el audio.';
      }
    });
  }

  // ════════════════════════════════════════════════════════
  // Exportación (Excel / PDF) y envío por correo
  // El archivo se genera en el BACKEND con el QBE actual del
  // formulario (hasta 1000 filas, no solo la página visible)
  // ════════════════════════════════════════════════════════

  exportarServidor(formato: 'excel' | 'pdf'): void {
    if (!this.entidad) return;
    this.exportando = formato;
    this.error = null;

    this.reporteService.exportarReporte(this.construirQBE(), formato).subscribe({
      next: (resp) => {
        this.exportando = null;
        // Nombre del archivo: viene en el header Content-Disposition
        const cd = resp.headers.get('Content-Disposition') ?? '';
        const nombre = /filename="?([^";]+)"?/.exec(cd)?.[1]
          ?? `reporte_${this.entidad}.${formato === 'excel' ? 'xlsx' : 'pdf'}`;
        // Descargar el blob como archivo
        const url = URL.createObjectURL(resp.body!);
        const a = document.createElement('a');
        a.href = url;
        a.download = nombre;
        a.click();
        URL.revokeObjectURL(url);
      },
      error: () => {
        this.exportando = null;
        this.error = 'No se pudo exportar el reporte.';
      }
    });
  }

  enviarCorreo(): void {
    const destino = this.correoDestino.trim();
    if (!destino || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(destino)) {
      this.error = 'Ingresa un correo electrónico válido.';
      return;
    }
    this.enviandoCorreo = true;
    this.error = null;
    this.correoExito = null;

    this.reporteService
      .enviarPorCorreo(this.construirQBE(), destino, this.correoFormato, this.correoMensaje.trim() || undefined)
      .subscribe({
        next: (res) => {
          this.enviandoCorreo = false;
          this.correoExito = `Reporte enviado a ${res.destinatario} (${res.archivo}, ${res.total_registros} registros).`;
          this.correoMensaje = '';
        },
        error: (err) => {
          this.enviandoCorreo = false;
          this.error = err?.error?.detail || 'No se pudo enviar el correo.';
        }
      });
  }

  exportarCSV(): void {
    if (!this.resultado?.filas.length) return;
    const cols = this.resultado.columnas;
    const escapar = (v: any) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const lineas = [
      cols.join(';'),
      ...this.resultado.filas.map(f => cols.map(c => escapar(f[c])).join(';'))
    ];
    const blob = new Blob(['﻿' + lineas.join('\n')], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `reporte_${this.entidad}_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }
}
