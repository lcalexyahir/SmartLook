// web/src/app/modules/assistant-admin/services/assistant-admin.service.ts
//
// NUEVO (CU20): consume el asistente de gestión para el personal.
//   POST /api/innovation/asistente/                                  { mensaje }
//   GET  /api/innovation/asistente/reportes/
//   GET  /api/innovation/asistente/reportes/:id/
//   GET  /api/innovation/asistente/reportes/:id/exportar/?formato=..  (blob)
// El token JWT lo agrega el JwtInterceptor global. El backend expone el
// nombre real del archivo en la cabecera Content-Disposition.
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export type FormatoReporte = 'pdf' | 'xlsx' | 'html';

export interface KpiResultado {
  etiqueta: string;
  valor: number | string;
  tipo: 'numero' | 'dinero' | 'texto';
}

export interface ColumnaResultado {
  nombre: string;
  tipo: 'numero' | 'dinero' | 'texto';
}

export interface ResultadoConsulta {
  titulo: string;
  subtitulo: string;
  kpis: KpiResultado[];
  columnas: ColumnaResultado[];
  filas: (string | number)[][];
  notas: string[];
}

export interface ReporteGenerado {
  id_reporte: number;
  consulta: string;
  resultado: ResultadoConsulta;
}

export interface RespuestaAsistenteAdmin {
  respuesta: string;
  resultados: ReporteGenerado[];
  proveedor: string;
  modelo: string;
}

export interface ReporteResumen {
  id_reporte: number;
  fecha: string;
  pregunta: string;
  titulo: string;
  consulta: string;
}

export interface ReporteDetalle {
  id_reporte: number;
  fecha: string;
  pregunta: string;
  consulta: string;
  respuesta: string;
  resultado: ResultadoConsulta;
}

@Injectable({
  providedIn: 'root'
})
export class AssistantAdminService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  preguntar(mensaje: string): Observable<RespuestaAsistenteAdmin> {
    return this.http.post<RespuestaAsistenteAdmin>(`${this.apiUrl}/innovation/asistente/`, { mensaje });
  }

  listarReportes(): Observable<ReporteResumen[]> {
    return this.http.get<ReporteResumen[]>(`${this.apiUrl}/innovation/asistente/reportes/`);
  }

  obtenerReporte(idReporte: number): Observable<ReporteDetalle> {
    return this.http.get<ReporteDetalle>(`${this.apiUrl}/innovation/asistente/reportes/${idReporte}/`);
  }

  // Devuelve el archivo (blob) junto con la respuesta completa, para leer el
  // nombre real desde Content-Disposition.
  descargarReporte(idReporte: number, formato: FormatoReporte): Observable<HttpEventBlobResponse> {
    return this.http.get(
      `${this.apiUrl}/innovation/asistente/reportes/${idReporte}/exportar/?formato=${formato}`,
      { observe: 'response', responseType: 'blob' }
    ) as unknown as Observable<HttpEventBlobResponse>;
  }
}

// Alias mínimo para no importar HttpResponse<Blob> en cada componente.
export type HttpEventBlobResponse = import('@angular/common/http').HttpResponse<Blob>;