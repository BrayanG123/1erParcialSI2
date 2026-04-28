export interface Vehiculo {
  id: number;
  cliente_id: number;
  placa: string;
  modelo: string;
  color: string;
  foto_vehiculo?: string;
  tipo_seguro?: string;
}

export interface VehiculoCreate {
  placa: string;
  modelo: string;
  color: string;
  foto_vehiculo?: string;
  tipo_seguro?: string;
}
