// Branch y Supplier se definen en branch.interface.ts; se reexportan aquí porque
// catalog.service.ts los importa desde este archivo.
export type { Branch, Supplier } from './branch.interface';
export interface Product {
  id_producto: number;
  categoria: Category;
  marca: Brand | null;
  temporada: Season | null;
  coleccion: Collection | null;
  nombre: string;
  descripcion: string;
  genero: string;
  tipo_prenda: string;
  imagen_producto: string | null;
  modelo_virtual: string | null;
  estado: string;
  variantes: ProductVariant[];
  // SaaS: tienda (empresa) dueña del producto. Solo lectura, la manda el backend.
  id_empresa?: number | null;
  empresa_nombre?: string | null;
}
export interface Category {
  id_categoria: number;
  nombre: string;
  descripcion: string;
  estado: boolean;
}
export interface Brand {
  id_marca: number;
  nombre: string;
  descripcion: string;
  estado: boolean;
}
export interface Season {
  id_temporada: number;
  nombre: string;
  descripcion: string;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  estado: boolean;
}
export interface Collection {
  id_coleccion: number;
  nombre: string;
  descripcion: string;
  anio: number | null;
  estado: boolean;
}
export interface ProductVariant {
  id_variante: number;
  talla: Size;
  color: Color;
  codigo_producto: string;
  precio: number;
  cantidad: number;
  imagen_variante: string | null;
  estado: string;
}
export interface Size {
  id_talla: number;
  nombre: string;
  descripcion: string;
  estado: boolean;
}
export interface Color {
  id_color: number;
  nombre: string;
  codigo_hex: string;
  estado: boolean;
}