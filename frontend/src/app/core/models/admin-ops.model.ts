export interface Servicio_Realizado {
  id: number;
  incidente_id?: number;
  mecanico_id?: number;
  mecanico_nombre?: string;
  cliente_nombre?: string;
  descripcion?: string;
  estado?: string;
  repuestos_usados?: string[] | string;
  observaciones_tecnicas?: string;
  costo_final?: number;
  fecha_finalizacion?: string;
}

export interface Evidencia_Item {
  id?: number;
  url?: string;
  archivo_url?: string;
  imagen_url?: string;
  foto_url?: string;
  descripcion?: string;
  fecha_creacion?: string;
}

export interface Comision_Servicio {
  id?: number;
  servicio_id?: number;
  mecanico_id?: number;
  porcentaje?: number;
  monto_comision?: number;
  comision?: number;
  monto?: number;
  fecha_emision?: string;
  fecha_pago?: string | null;
}

export interface Pago_Request {
  servicio_id: number;
  metodo: 'efectivo' | 'pasarela';
  referencia?: string;
}

export interface Bitacora_Evento {
  id?: number;
  usuario_id?: number;
  evento?: string;
  accion?: string;
  descripcion?: string;
  usuario?: string;
  fecha?: string;
  fecha_creacion?: string;
}

