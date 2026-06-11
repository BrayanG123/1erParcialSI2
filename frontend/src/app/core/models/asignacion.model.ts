export interface AsignacionRequest {
  incidente_id: number;
  mecanico_id?: number;
  notas?: string;
}

export interface AsignacionResponse {
  id: number;
  incidente_id: number;
  mecanico_id: number;
  fecha_asignacion: string;
  estado: string;
}
