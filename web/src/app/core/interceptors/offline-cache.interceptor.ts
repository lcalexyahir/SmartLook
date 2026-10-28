// web/src/app/core/interceptors/offline-cache.interceptor.ts
//
// NUEVO (SaaS - A.5/A.6): consulta del catálogo sin conexión.
// Cada respuesta correcta de las consultas de catálogo, disponibilidad por
// sucursal y reservas se guarda en IndexedDB (almacén "cache") con la fecha
// en que se descargó. Si después la misma consulta falla por falta de red,
// se responde con esa copia y se avisa a ConexionService para que la barra
// superior indique que la información puede estar desactualizada.
// Solo se guardan consultas GET de lectura; nunca operaciones que cambian datos.
import { Injectable } from '@angular/core';
import {
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
  HttpResponse
} from '@angular/common/http';
import { Observable, from, of, throwError } from 'rxjs';
import { catchError, switchMap, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { ConexionService } from '../services/conexion.service';
import { ALMACEN_CACHE, OfflineDbService } from '../services/offline-db.service';

// Consultas que se pueden ver sin conexión (productos, precios, tallas,
// colores, disponibilidad por sucursal y las reservas del cliente).
const RUTAS_CON_COPIA = [
  '/catalog/productos/',
  '/catalog/categorias/',
  '/catalog/marcas/',
  '/catalog/tallas/',
  '/catalog/colores/',
  '/catalog/sucursales/',
  '/inventory/stock/',
  '/reservations/reservas/'
];

interface CopiaHttp {
  clave: string;
  fecha: string;
  datos: any;
}

@Injectable()
export class OfflineCacheInterceptor implements HttpInterceptor {
  constructor(private db: OfflineDbService, private conexion: ConexionService) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    if (request.method !== 'GET' || !request.url.startsWith(environment.apiUrl)) {
      return next.handle(request);
    }
    const ruta = request.url.slice(environment.apiUrl.length);
    // "_ping" lo usa el POS para comprobar si el servidor volvió: nunca se responde con copia.
    const conCopia = RUTAS_CON_COPIA.some(r => ruta.startsWith(r)) && !request.params.has('_ping');
    if (!conCopia) {
      return next.handle(request).pipe(
        tap(evento => {
          if (evento instanceof HttpResponse) {
            this.conexion.respuestaDelServidor();
          }
        })
      );
    }
    const clave = `http:${this.usuarioActual()}:${request.urlWithParams}`;
    return next.handle(request).pipe(
      tap(evento => {
        if (evento instanceof HttpResponse && evento.status === 200) {
          this.conexion.respuestaDelServidor();
          const copia: CopiaHttp = { clave, fecha: new Date().toISOString(), datos: evento.body };
          this.db.guardar(ALMACEN_CACHE, copia).catch(() => undefined);
        }
      }),
      catchError(err => {
        if (!this.conexion.esErrorDeRed(err)) {
          return throwError(() => err);
        }
        return from(this.db.obtener<CopiaHttp>(ALMACEN_CACHE, clave).catch(() => undefined)).pipe(
          switchMap(copia => {
            if (!copia) {
              return throwError(() => err);
            }
            this.conexion.usandoCopiaLocal(copia.fecha);
            return of(new HttpResponse({ status: 200, body: copia.datos, url: request.urlWithParams }));
          })
        );
      })
    );
  }

  private usuarioActual(): string {
    try {
      const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');
      return String(usuario?.id_usuario ?? 'anonimo');
    } catch {
      return 'anonimo';
    }
  }
}