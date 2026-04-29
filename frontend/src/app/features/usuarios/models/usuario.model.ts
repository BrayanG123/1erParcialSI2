export type RolUsuario = 'superadmin' | 'administrador' | 'mecanico' | 'cliente';

export interface Usuario {
  id: number;
  nombre: string;
  apellido: string;
  email: string;
  username: string;
  rol: RolUsuario;
  is_active: boolean;
  fecha_creacion: string;
}
