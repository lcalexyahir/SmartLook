export interface StockItem {
  id_stock: number;
  sucursal: string;
  variante: string;
  id_sucursal: number;
  sucursal_nombre: string;
  ciudad: string;
  direccion: string;
  cantidad: number;
  disponible: boolean;
  stock_minimo: number;
  stock_maximo: number;
  estado: boolean;
  fecha_actualizacion: string;
}

export interface InventoryMovement {
  id_movimiento: number;
  sucursal: string;
  variante: string;
  usuario: string;
  tipo_movimiento: string;
  cantidad: number;
  motivo: string | null;
  fecha_movimiento: string;
}