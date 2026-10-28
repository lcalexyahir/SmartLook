// web/src/app/core/services/conexion.service.ts
//
// NUEVO (SaaS - A.5/A.6): estado de la conexión para toda la aplicación.
// - enLinea$: lo que informa el navegador (eventos online / offline).
// - copiaLocal$: fecha de la información guardada en el dispositivo que se
//   está mostrando porque el servidor no respondió (la usa la barra superior
//   para avisar que puede estar desactualizada). Vuelve a null en cuanto el
//   servidor responde otra vez.
// - esErrorDeRed(): reconoce un fallo de red. Sin service worker llega con
//   status 0; con el service worker de la PWA, como 504 (Gateway Timeout).
// - nuevoUuid(): identificador único de cada operación hecha sin conexión.
import { Injectable } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject } from 'rxjs';

// UUID v4. crypto.randomUUID solo existe en https o localhost; si la web se
// abre por la IP de la red (http), se arma el UUID con getRandomValues.
export function nuevoUuid(): string {
  const c: Crypto = window.crypto;
  if (typeof c.randomUUID === 'function') {
    return c.randomUUID();
  }
  const bytes: Uint8Array = c.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (b: number) => b.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function esErrorDeRed(err: any): boolean {
  return err instanceof HttpErrorResponse && (err.status === 0 || err.status === 504);
}

@Injectable({
  providedIn: 'root'
})
export class ConexionService {
  private enLineaSubject = new BehaviorSubject<boolean>(navigator.onLine);
  enLinea$ = this.enLineaSubject.asObservable();
  private copiaSubject = new BehaviorSubject<string | null>(null);
  copiaLocal$ = this.copiaSubject.asObservable();

  constructor() {
    window.addEventListener('online', () => this.enLineaSubject.next(true));
    window.addEventListener('offline', () => this.enLineaSubject.next(false));
  }

  get enLinea(): boolean {
    return this.enLineaSubject.value;
  }

  esErrorDeRed(err: any): boolean {
    return esErrorDeRed(err);
  }

  // Se mostró información guardada: se recuerda la fecha más antigua.
  usandoCopiaLocal(fecha: string): void {
    const actual = this.copiaSubject.value;
    if (!actual || fecha < actual) {
      this.copiaSubject.next(fecha);
    }
  }

  // El servidor respondió: la información que se ve ya es la actual.
  respuestaDelServidor(): void {
    if (this.copiaSubject.value !== null) {
      this.copiaSubject.next(null);
    }
  }
}