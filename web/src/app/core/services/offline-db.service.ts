// web/src/app/core/services/offline-db.service.ts
//
// NUEVO (SaaS - A.5): almacenamiento local del navegador con IndexedDB para
// trabajar sin conexión. Los datos sobreviven al cerrar y volver a abrir la
// aplicación (a diferencia de la memoria de la página).
// Almacenes:
// - ventas_pendientes: ventas POS hechas sin conexión (clave: uuid).
// - cache: copias de datos del servidor para consultar sin conexión, como
//   el catálogo del POS o las sucursales (clave: "clave").
// MODIFICADO (A.5 - reservas): versión 2 de la base, agrega el almacén
// reservas_pendientes (reservas de prendas hechas sin conexión, clave: uuid).
// Las bases que ya existían en versión 1 se actualizan solas sin perder datos.
import { Injectable } from '@angular/core';

const NOMBRE_BD = 'smartlook-offline';
const VERSION_BD = 2;
export const ALMACEN_VENTAS = 'ventas_pendientes';
export const ALMACEN_CACHE = 'cache';
export const ALMACEN_RESERVAS = 'reservas_pendientes';

@Injectable({
  providedIn: 'root'
})
export class OfflineDbService {
  private bd: Promise<IDBDatabase> | null = null;

  // Abre la base una sola vez y crea los almacenes la primera vez.
  private abrir(): Promise<IDBDatabase> {
    if (!this.bd) {
      this.bd = new Promise((resolve, reject) => {
        if (!('indexedDB' in window)) {
          reject(new Error('Este navegador no permite guardar datos sin conexión.'));
          return;
        }
        const solicitud = indexedDB.open(NOMBRE_BD, VERSION_BD);
        solicitud.onupgradeneeded = () => {
          const bd = solicitud.result;
          if (!bd.objectStoreNames.contains(ALMACEN_VENTAS)) {
            bd.createObjectStore(ALMACEN_VENTAS, { keyPath: 'uuid' });
          }
          if (!bd.objectStoreNames.contains(ALMACEN_CACHE)) {
            bd.createObjectStore(ALMACEN_CACHE, { keyPath: 'clave' });
          }
          if (!bd.objectStoreNames.contains(ALMACEN_RESERVAS)) {
            bd.createObjectStore(ALMACEN_RESERVAS, { keyPath: 'uuid' });
          }
        };
        solicitud.onsuccess = () => resolve(solicitud.result);
        solicitud.onerror = () => {
          this.bd = null;
          reject(solicitud.error);
        };
      });
    }
    return this.bd;
  }

  private async ejecutar<T>(
    almacen: string,
    modo: IDBTransactionMode,
    accion: (store: IDBObjectStore) => IDBRequest
  ): Promise<T> {
    const bd = await this.abrir();
    return new Promise<T>((resolve, reject) => {
      const transaccion = bd.transaction(almacen, modo);
      const solicitud = accion(transaccion.objectStore(almacen));
      transaccion.oncomplete = () => resolve(solicitud.result as T);
      transaccion.onerror = () => reject(transaccion.error);
      transaccion.onabort = () => reject(transaccion.error);
    });
  }

  guardar<T>(almacen: string, valor: T): Promise<IDBValidKey> {
    return this.ejecutar(almacen, 'readwrite', store => store.put(valor));
  }

  obtener<T>(almacen: string, clave: IDBValidKey): Promise<T | undefined> {
    return this.ejecutar(almacen, 'readonly', store => store.get(clave));
  }

  todos<T>(almacen: string): Promise<T[]> {
    return this.ejecutar(almacen, 'readonly', store => store.getAll());
  }

  eliminar(almacen: string, clave: IDBValidKey): Promise<void> {
    return this.ejecutar(almacen, 'readwrite', store => store.delete(clave));
  }
}