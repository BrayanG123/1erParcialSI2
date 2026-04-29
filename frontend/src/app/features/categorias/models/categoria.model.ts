export interface Categoria_Item {
  id: number;
  nombre: string;
  descripcion?: string;
  prioridad: number;
  is_active?: boolean;
}

export interface Categoria_Create_Request {
  nombre: string;
  descripcion?: string;
  prioridad: number;
}
