// web/src/app/modules/assistant/services/assistant.service.ts
//
// NUEVO (CU18/CU19): consume el asistente virtual del cliente.
//   POST /api/innovation/chatbot/            { mensaje }
//   GET  /api/innovation/chatbot/historial/
// El token JWT lo agrega el JwtInterceptor global.
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

// Prenda sugerida por el asistente (tarjeta que se muestra en el chat).
export interface TarjetaPrenda {
  id_producto: number;
  nombre: string;
  categoria: string;
  temporada: string | null;
  precio_desde: number;
  precio_hasta: number;
  tallas: string[];
  colores: string[];
  sucursales: string[];
  imagen: string | null;
}

export interface RespuestaAsistente {
  respuesta: string;
  tarjetas: TarjetaPrenda[];
  proveedor: string;
  modelo: string;
}

// Un intercambio guardado (el historial no conserva las tarjetas).
export interface MensajeHistorial {
  id: number;
  mensaje: string;
  respuesta: string;
  fecha: string;
}

@Injectable({
  providedIn: 'root'
})
export class AssistantService {
  constructor(private apiService: ApiService) {}

  enviar(mensaje: string): Observable<RespuestaAsistente> {
    return this.apiService.post<RespuestaAsistente>('/innovation/chatbot/', { mensaje });
  }

  historial(): Observable<MensajeHistorial[]> {
    return this.apiService.get<MensajeHistorial[]>('/innovation/chatbot/historial/');
  }
}