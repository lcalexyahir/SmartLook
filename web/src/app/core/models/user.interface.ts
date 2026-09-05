export interface User {
  id_usuario: number;
  nombres: string;
  apellidos: string;
  correo: string;
  telefono: string;
  estado: string;
  ultimo_acceso: string | null;
  fecha_creacion: string;
  roles: Role[];
}

export interface Role {
  id_rol: number;
  nombre: string;
  descripcion: string;
  estado: boolean;
}

export interface Permiso {
  id_permiso: number;
  nombre: string;
  descripcion: string;
  estado: boolean;
}