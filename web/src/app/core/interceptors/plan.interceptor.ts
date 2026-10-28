// web/src/app/core/interceptors/plan.interceptor.ts
//
// NUEVO (SaaS - A.3): reconoce los errores de plan que devuelve el backend
// ({"detail": "...", "codigo": "plan_no_permitido" | "suscripcion_vencida"})
// y los muestra como aviso en el panel. El error sigue su curso normal, así
// cada pantalla puede además mostrar su propio mensaje.
import { Injectable } from '@angular/core';
import {
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AvisoPlanService } from '../services/aviso-plan.service';

const CODIGOS_PLAN = ['plan_no_permitido', 'suscripcion_vencida'];

@Injectable()
export class PlanInterceptor implements HttpInterceptor {
  constructor(private avisoPlan: AvisoPlanService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(req).pipe(
      catchError((err: unknown) => {
        if (err instanceof HttpErrorResponse) {
          const codigo = err.error?.codigo;
          if (CODIGOS_PLAN.includes(codigo)) {
            this.avisoPlan.mostrar({
              codigo,
              mensaje: String(err.error?.detail || 'Tu plan no permite esta operación.')
            });
          }
        }
        return throwError(() => err);
      })
    );
  }
}