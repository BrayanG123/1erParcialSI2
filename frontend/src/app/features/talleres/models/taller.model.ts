export interface Taller {
  id: number;
  nombre: string;
  direccion: string;
  telefono?: string;
  latitud?: number;
  longitud?: number;
}

export interface TallerGlobalRow {
  id: number;
  nombre: string;
  direccion: string;
  telefono: string | null;
  latitud: number | null;
  longitud: number | null;
  calificacion_promedio: number | null;
  administrador_id: number | null;
  administrador_usuario_id: number | null;
  is_active: boolean;
}
