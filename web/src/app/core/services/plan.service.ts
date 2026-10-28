// web/src/app/core/services/plan.service.ts
//
// NUEVO (SaaS - A.3): suscripción de la empresa del usuario (plan, uso y
// vencimiento). La carga el layout al entrar al panel y la usa para ocultar
// lo que el plan no incluye (por ejemplo, el asistente IA) y para avisar
// cuando la suscripción vence. Para el SUPER_ADMIN y los clientes el backend
// responde 404 (no tienen empresa) y aquí queda en null: no se oculta nada.
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { ApiService } from './api.service';

@Injectable({
  providedIn: 'root'
})
export class PlanService {
  private suscripcionSubject = new BehaviorSubject<any | null>(null);
  suscripcion$ = this.suscripcionSubject.asObservable();

  constructor(private api: ApiService) {}

  get suscripcion(): any | null {
    return this.suscripcionSubject.value;
  }

  cargar(): Observable<any | null> {
    return this.api.get<any>('/auth/suscripciones/actual/').pipe(
      tap(suscripcion => this.suscripcionSubject.next(suscripcion)),
      catchError(() => {
        this.suscripcionSubject.next(null);
        return of(null);
      })
    );
  }

  // true si el plan incluye la función (ej. 'reportes_ia'). Sin suscripción
  // cargada no se oculta nada: el backend sigue siendo quien decide.
  incluye(funcion: string): boolean {
    const plan = this.suscripcion?.plan;
    return plan ? !!plan[funcion] : true;
  }

  limpiar(): void {
    this.suscripcionSubject.next(null);
  }
}