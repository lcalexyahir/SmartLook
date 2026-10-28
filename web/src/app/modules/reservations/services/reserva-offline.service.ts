// web/src/app/modules/reservations/services/reserva-offline.service.ts
//
// NUEVO (SaaS - A.5): reservas de prendas hechas sin conexión (cliente).
// - Cola local (IndexedDB, almacén reservas_pendientes). Cada reserva lleva
//   un UUID propio y la hora en que se hizo.
// - Estados (punto 5.4 del enunciado, igual que las ventas del POS):
//     REGISTRADA  -> guardada en el dispositivo, aún no enviada.
//     ENVIADA     -> enviada al servidor, esperando su respuesta.
//     CONFIRMADA  -> el servidor la registró (queda con su número de reserva).
//     RECHAZADA   -> el servidor no la aceptó (queda con el motivo).
//   Una reserva nunca se borra solo por haberse intentado enviar: si el envío
//   falla vuelve a REGISTRADA (el UUID evita duplicados al reenviarla).
// - Se envían a POST /api/reservations/reservas/sync/ al recuperar internet,
//   al entrar a la aplicación o con el botón "Sincronizar ahora".
import { Injectable } from '@angular/core';
import { BehaviorSubject, firstValueFrom } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { esErrorDeRed, nuevoUuid } from '../../../core/services/conexion.service';
import { ALMACEN_RESERVAS, OfflineDbService } from '../../../core/services/offline-db.service';

export type EstadoReservaLocal = 'REGISTRADA' | 'ENVIADA' | 'CONFIRMADA' | 'RECHAZADA';

export interface ItemReservaLocal {
  id_variante: number;
  label: string;
}

export interface ReservaLocal {
  uuid: string;
  fecha_operacion: string;
  id_sucursal: number;
  sucursal: string;
  fecha_reserva: string;
  hora_reserva: string;
  items: ItemReservaLocal[];
  estado: EstadoReservaLocal;
  mensaje: string | null;
  intentos: number;
  id_usuario: number | null;
  id_reserva: number | null;
  fecha_confirmacion: string | null;
}

export interface ResultadoSyncReservas {
  sincronizadas: number;
  duplicadas: number;
  rechazadas: number;
  error: string | null;
  fecha: string;
}

const MAX_POR_LOTE = 100;

function porEnviar(reserva: ReservaLocal): boolean {
  return reserva.estado === 'REGISTRADA' || reserva.estado === 'ENVIADA';
}

@Injectable({
  providedIn: 'root'
})
export class ReservaOfflineService {
  private reservasSubject = new BehaviorSubject<ReservaLocal[]>([]);
  reservas$ = this.reservasSubject.asObservable();
  private sincronizandoSubject = new BehaviorSubject<boolean>(false);
  sincronizando$ = this.sincronizandoSubject.asObservable();
  private resultadoSubject = new BehaviorSubject<ResultadoSyncReservas | null>(null);
  resultado$ = this.resultadoSubject.asObservable();

  constructor(private db: OfflineDbService, private api: ApiService) {
    window.addEventListener('online', () => this.sincronizar());
    this.recargar();
  }

  private usuarioActual(): number | null {
    try {
      const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');
      return usuario?.id_usuario ?? null;
    } catch {
      return null;
    }
  }

  // Reservas locales del usuario de la sesión.
  private async reservasDelUsuario(): Promise<ReservaLocal[]> {
    const usuario = this.usuarioActual();
    const reservas = await this.db.todos<ReservaLocal>(ALMACEN_RESERVAS);
    return reservas.filter(r => r.id_usuario === usuario);
  }

  // Para mostrar: las más recientes primero.
  async recargar(): Promise<void> {
    try {
      const reservas = await this.reservasDelUsuario();
      this.reservasSubject.next(reservas.sort((a, b) => b.fecha_operacion.localeCompare(a.fecha_operacion)));
    } catch {
      this.reservasSubject.next([]);
    }
  }

  async guardar(datos: {
    id_sucursal: number;
    sucursal: string;
    fecha_reserva: string;
    hora_reserva: string;
    items: ItemReservaLocal[];
  }): Promise<ReservaLocal> {
    const reserva: ReservaLocal = {
      uuid: nuevoUuid(),
      fecha_operacion: new Date().toISOString(),
      id_sucursal: datos.id_sucursal,
      sucursal: datos.sucursal,
      fecha_reserva: datos.fecha_reserva,
      hora_reserva: datos.hora_reserva,
      items: datos.items.map(i => ({ ...i })),
      estado: 'REGISTRADA',
      mensaje: null,
      intentos: 0,
      id_usuario: this.usuarioActual(),
      id_reserva: null,
      fecha_confirmacion: null
    };
    await this.db.guardar(ALMACEN_RESERVAS, reserva);
    await this.recargar();
    return reserva;
  }

  // Solo se descartan las rechazadas, después de que el cliente leyó el motivo.
  async descartar(reserva: ReservaLocal): Promise<void> {
    if (reserva.estado !== 'RECHAZADA') {
      return;
    }
    await this.db.eliminar(ALMACEN_RESERVAS, reserva.uuid);
    await this.recargar();
  }

  // Quita del dispositivo el historial de reservas ya confirmadas por el servidor.
  async limpiarConfirmadas(): Promise<void> {
    const reservas = await this.reservasDelUsuario();
    for (const reserva of reservas.filter(r => r.estado === 'CONFIRMADA')) {
      await this.db.eliminar(ALMACEN_RESERVAS, reserva.uuid);
    }
    await this.recargar();
  }

  async sincronizar(): Promise<ResultadoSyncReservas | null> {
    if (this.sincronizandoSubject.value || !navigator.onLine || !localStorage.getItem('access_token')) {
      return null;
    }
    let pendientes: ReservaLocal[];
    try {
      pendientes = (await this.reservasDelUsuario())
        .filter(porEnviar)
        .sort((a, b) => a.fecha_operacion.localeCompare(b.fecha_operacion));
    } catch {
      return null;
    }
    if (pendientes.length === 0) {
      return null;
    }
    this.sincronizandoSubject.next(true);
    const resultado: ResultadoSyncReservas = {
      sincronizadas: 0, duplicadas: 0, rechazadas: 0, error: null, fecha: new Date().toISOString()
    };
    try {
      for (let i = 0; i < pendientes.length; i += MAX_POR_LOTE) {
        await this.enviarLote(pendientes.slice(i, i + MAX_POR_LOTE), resultado);
      }
    } catch (err) {
      resultado.error = this.textoError(err);
    } finally {
      this.sincronizandoSubject.next(false);
      this.resultadoSubject.next(resultado);
      await this.recargar();
    }
    return resultado;
  }

  private async enviarLote(lote: ReservaLocal[], resultado: ResultadoSyncReservas): Promise<void> {
    for (const reserva of lote) {
      reserva.estado = 'ENVIADA';
      reserva.intentos += 1;
      await this.db.guardar(ALMACEN_RESERVAS, reserva);
    }
    await this.recargar();
    let respuesta: any;
    try {
      respuesta = await firstValueFrom(this.api.post<any>('/reservations/reservas/sync/', {
        operaciones: lote.map(r => ({
          uuid: r.uuid,
          fecha_operacion: r.fecha_operacion,
          id_sucursal: r.id_sucursal,
          fecha_reserva: r.fecha_reserva,
          hora_reserva: r.hora_reserva,
          items: r.items.map(i => ({ id_variante: i.id_variante }))
        }))
      }));
    } catch (err) {
      // No llegó respuesta válida: todo el lote vuelve a REGISTRADA para reintentar.
      for (const reserva of lote) {
        reserva.estado = 'REGISTRADA';
        await this.db.guardar(ALMACEN_RESERVAS, reserva);
      }
      throw err;
    }
    const porUuid = new Map<string, ReservaLocal>(lote.map(r => [r.uuid, r] as [string, ReservaLocal]));
    for (const r of respuesta?.resultados || []) {
      const reserva = r.uuid ? porUuid.get(r.uuid) : undefined;
      if (!reserva) {
        continue;
      }
      porUuid.delete(r.uuid);
      if (r.estado === 'SINCRONIZADA' || r.estado === 'DUPLICADA') {
        reserva.estado = 'CONFIRMADA';
        reserva.id_reserva = r.id_reserva ?? null;
        reserva.fecha_confirmacion = new Date().toISOString();
        reserva.mensaje = r.estado === 'DUPLICADA' ? 'Ya estaba registrada en el servidor.' : null;
        if (r.estado === 'SINCRONIZADA') {
          resultado.sincronizadas += 1;
        } else {
          resultado.duplicadas += 1;
        }
      } else {
        reserva.estado = 'RECHAZADA';
        reserva.mensaje = r.mensaje || 'El servidor rechazó la reserva.';
        resultado.rechazadas += 1;
      }
      await this.db.guardar(ALMACEN_RESERVAS, reserva);
    }
    // Las que no vinieron en la respuesta se reintentan después.
    for (const reserva of porUuid.values()) {
      reserva.estado = 'REGISTRADA';
      await this.db.guardar(ALMACEN_RESERVAS, reserva);
    }
  }

  private textoError(err: any): string {
    if (esErrorDeRed(err)) {
      return 'Sin conexión con el servidor. Las reservas siguen guardadas y se enviarán después.';
    }
    if (err?.status === 401) {
      return 'Tu sesión expiró. Inicia sesión de nuevo para enviar las reservas pendientes.';
    }
    return err?.error?.detail || err?.error?.error || 'No se pudieron enviar las reservas pendientes.';
  }
}