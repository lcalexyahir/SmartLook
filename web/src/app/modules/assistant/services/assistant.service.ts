// web/src/app/modules/assistant/services/assistant.service.ts
//
// NUEVO (CU18/CU19): consume el asistente virtual del cliente.
//   POST /api/innovation/chatbot/            { mensaje }
//   GET  /api/innovation/chatbot/historial/
// El token JWT lo agrega el JwtInterceptor global.
// MODIFICADO (chat por sesión): la conversación vive solo en memoria (aquí, en
// el servicio): se mantiene al moverse por la web y se borra al recargar la
// página o cerrarla. Ya no se carga el historial guardado; cada mensaje lleva
// los últimos intercambios de la conversación abierta como contexto.
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

// NUEVO: un intercambio de la conversación abierta (contexto para el asistente).
export interface IntercambioChat {
  mensaje: string;
  respuesta: string;
}

// NUEVO: mensaje del chat tal como se muestra (vive en este servicio).
export interface ParteTexto {
  texto: string;
  negrita: boolean;
}

export interface MensajeChat {
  autor: 'cliente' | 'asistente';
  texto: string;
  partes: ParteTexto[];
  tarjetas: TarjetaPrenda[];
  error: boolean;
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
  // NUEVO: conversación abierta (solo en memoria; se pierde al recargar).
  readonly mensajes: MensajeChat[] = [];

  constructor(private apiService: ApiService) {}

  enviar(mensaje: string, historial: IntercambioChat[] = []): Observable<RespuestaAsistente> {
    return this.apiService.post<RespuestaAsistente>('/innovation/chatbot/', { mensaje, historial });
  }

  /** NUEVO: últimos intercambios completos (pregunta + respuesta sin error). */
  intercambiosRecientes(maximo = 4): IntercambioChat[] {
    const pares: IntercambioChat[] = [];
    for (let i = 0; i < this.mensajes.length - 1; i++) {
      const pregunta = this.mensajes[i];
      const respuesta = this.mensajes[i + 1];
      if (pregunta.autor === 'cliente' && respuesta.autor === 'asistente' && !respuesta.error) {
        pares.push({ mensaje: pregunta.texto, respuesta: respuesta.texto });
      }
    }
    return pares.slice(-maximo);
  }

  historial(): Observable<MensajeHistorial[]> {
    return this.apiService.get<MensajeHistorial[]>('/innovation/chatbot/historial/');
  }
}