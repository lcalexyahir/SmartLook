// web/src/app/core/services/aviso-plan.service.ts
//
// NUEVO (SaaS - A.3): aviso que se muestra en la parte superior del panel
// cuando el backend rechaza una operación por el plan (403 plan_no_permitido)
// o por la suscripción vencida (402 suscripcion_vencida). Es un servicio sin
// dependencias para que el interceptor HTTP pueda usarlo sin crear un ciclo.
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export type CodigoPlan = 'plan_no_permitido' | 'suscripcion_vencida';

export interface AvisoPlan {
  codigo: CodigoPlan;
  mensaje: string;
}

@Injectable({
  providedIn: 'root'
})
export class AvisoPlanService {
  private avisoSubject = new BehaviorSubject<AvisoPlan | null>(null);
  aviso$ = this.avisoSubject.asObservable();

  mostrar(aviso: AvisoPlan): void {
    this.avisoSubject.next(aviso);
  }

  cerrar(): void {
    this.avisoSubject.next(null);
  }
}