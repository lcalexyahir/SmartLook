export interface Country {
  id_pais: number;
  nombre: string;
  estado: boolean;
}

export interface City {
  id_ciudad: number;
  pais: Country;
  nombre: string;
  estado: boolean;
}

export interface Branch {
  id_sucursal: number;
  ciudad: City;
  nombre: string;
  direccion: string;
  telefono: string | null;
  estado: string;
  fecha_apertura: string | null;
}

export interface Supplier {
  id_proveedor: number;
  nombre_empresa: string;
  nombre_contacto: string | null;
  telefono: string | null;
  correo: string | null;
  direccion: string | null;
  estado: string;
}