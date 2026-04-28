export interface Incidente {
  id: number;
  descripcion: string;
  latitud: number;       // ✅ era ubicacion_lat
  longitud: number;      // ✅ era ubicacion_lng
  vehiculo_id: number;
  categoria_id: number;
  fecha_hora: string;    // ✅ era fecha_creacion
  estado: string;
  resumen_ia: string;
  cliente_id: number;
  // taller_id no existe en el backend, removido
}
