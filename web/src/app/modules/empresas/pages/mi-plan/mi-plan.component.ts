// web/src/app/modules/empresas/pages/mi-plan/mi-plan.component.ts
//
// NUEVO (SaaS - A.3): "Mi plan" del ADMIN_EMPRESA.
// - Plan actual, estado, vencimiento, días restantes y uso de los límites.
// - Planes disponibles con precio en USD y Bs; renovar el mismo plan o
//   cambiar a otro pagando con Stripe en modo test (4242 4242 4242 4242).
// - Historial de pagos de la suscripción.
// Reglas del backend: renovar el mismo plan vigente suma un periodo al
// vencimiento; cambiar de plan (o renovar uno vencido) empieza hoy.
import { Component, OnDestroy, OnInit } from '@angular/core';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { loadStripe, Stripe, StripeCardElement } from '@stripe/stripe-js';
import { environment } from '../../../../../environments/environment';
import { ApiService } from '../../../../core/services/api.service';
import { PlanService } from '../../../../core/services/plan.service';
import { formatoFecha, mensajeDeError } from '../../services/empresa.service';

const TEXTO_PERIODO: { [periodo: string]: string } = {
  MENSUAL: 'mes',
  SEMESTRAL: 'semestre',
  ANUAL: 'año'
};

const FUNCIONES = [
  { clave: 'delivery', texto: 'Delivery a domicilio' },
  { clave: 'vestidor_virtual', texto: 'Vestidor virtual' },
  { clave: 'chatbot_clientes', texto: 'Chatbot para clientes' },
  { clave: 'reportes_ia', texto: 'Asistente y reportes con IA' },
  { clave: 'comparativo_sucursales', texto: 'Comparativo entre sucursales' },
  { clave: 'modo_offline', texto: 'Modo sin conexión' }
];

const LIMITES = [
  { clave: 'max_sucursales', uso: 'sucursales', texto: 'Sucursales' },
  { clave: 'max_personal', uso: 'personal', texto: 'Personal' },
  { clave: 'max_productos', uso: 'productos', texto: 'Productos' }
];

@Component({
  selector: 'app-mi-plan',
  template: `
    <div class="plan-container">
      <h2>Mi plan</h2>
      <p *ngIf="cargando">Cargando suscripción...</p>
      <p class="error" *ngIf="error">{{ error }}</p>
      <p class="exito" *ngIf="mensajeExito">{{ mensajeExito }}</p>

      <ng-container *ngIf="suscripcion as s">
        <section class="card actual">
          <div class="actual-head">
            <div>
              <span class="etiqueta">Plan actual</span>
              <h3>{{ s.plan.nombre }}</h3>
              <p class="muted">{{ s.empresa }}</p>
            </div>
            <span class="badge" [class.badge--ok]="s.vigente" [class.badge--mal]="!s.vigente">
              {{ s.vigente ? 'ACTIVA' : 'VENCIDA' }}
            </span>
          </div>
          <div class="fechas">
            <div><span class="muted">Inicio</span><strong>{{ formatoFecha(s.fecha_inicio) }}</strong></div>
            <div><span class="muted">Vencimiento</span><strong>{{ formatoFecha(s.fecha_vencimiento) }}</strong></div>
            <div>
              <span class="muted">Tiempo restante</span>
              <strong [class.alerta]="s.dias_restantes <= 7">
                {{ s.dias_restantes < 0 ? 'Vencida' : s.dias_restantes + ' días' }}
              </strong>
            </div>
          </div>
          <div class="uso">
            <div class="uso-fila" *ngFor="let l of limites">
              <div class="uso-texto">
                <span>{{ l.texto }}</span>
                <span>{{ s.uso[l.uso] }} / {{ s.plan[l.clave] ?? 'Ilimitado' }}</span>
              </div>
              <div class="barra">
                <div class="barra-relleno" [style.width.%]="porcentaje(s.uso[l.uso], s.plan[l.clave])"
                     [class.barra--llena]="porcentaje(s.uso[l.uso], s.plan[l.clave]) >= 100"></div>
              </div>
            </div>
          </div>
          <ul class="funciones">
            <li *ngFor="let f of funciones" [class.no]="!s.plan[f.clave]">
              <span class="marca">{{ s.plan[f.clave] ? '✓' : '✕' }}</span>{{ f.texto }}
            </li>
          </ul>
        </section>

        <h3 class="subtitulo">Planes disponibles</h3>
        <div class="planes">
          <section class="card plan" *ngFor="let p of planes" [class.plan--actual]="p.id_plan === s.plan.id_plan">
            <span class="actual-tag" *ngIf="p.id_plan === s.plan.id_plan">Tu plan</span>
            <h4>{{ p.nombre }}</h4>
            <p class="precio">USD {{ numero(p.precio_usd) }} <span>/ {{ textoPeriodo(p.periodo) }}</span></p>
            <p class="precio-bs">Bs {{ numero(p.precio_bob) }}</p>
            <ul class="limites">
              <li *ngFor="let l of limites">{{ l.texto }}: {{ p[l.clave] ?? 'Ilimitado' }}</li>
            </ul>
            <ul class="funciones funciones--chicas">
              <li *ngFor="let f of funciones" [class.no]="!p[f.clave]">
                <span class="marca">{{ p[f.clave] ? '✓' : '✕' }}</span>{{ f.texto }}
              </li>
            </ul>
            <p class="nota" *ngIf="motivoNoDisponible(p, s) as motivo">{{ motivo }}</p>
            <p class="nota" *ngIf="!motivoNoDisponible(p, s)">{{ textoEfecto(p, s) }}</p>
            <button type="button" class="btn btn-primary btn-bloque"
                    [disabled]="!!motivoNoDisponible(p, s) || !!planEnPago || iniciando"
                    (click)="iniciarPago(p)">
              {{ p.id_plan === s.plan.id_plan ? 'Renovar' : 'Cambiar a ' + p.nombre }}
            </button>
          </section>
        </div>

        <section class="card pago" *ngIf="planEnPago as p">
          <h3>Pagar {{ p.nombre }}: USD {{ numero(p.precio_usd) }} (Bs {{ numero(p.precio_bob) }})</h3>
          <label class="etiqueta">Datos de la tarjeta</label>
          <div id="tarjeta-plan" class="tarjeta"></div>
          <p class="muted">Tarjeta de prueba: 4242 4242 4242 4242, cualquier fecha futura y CVC.</p>
          <p class="error" *ngIf="errorPago">{{ errorPago }}</p>
          <div class="pago-acciones">
            <button type="button" class="btn btn-primary" [disabled]="confirmando" (click)="confirmarPago()">
              {{ confirmando ? 'Procesando pago...' : 'Pagar USD ' + numero(p.precio_usd) }}
            </button>
            <button type="button" class="btn btn-link" [disabled]="confirmando" (click)="cancelarPago()">Cancelar</button>
          </div>
        </section>

        <section class="card">
          <h3>Historial de pagos</h3>
          <p class="muted" *ngIf="pagos.length === 0">Todavía no hay pagos registrados.</p>
          <div class="tabla-wrap" *ngIf="pagos.length > 0">
            <table class="tabla">
              <thead>
                <tr><th>Fecha</th><th>Plan</th><th>USD</th><th>Bs</th><th>Estado</th><th>Referencia</th></tr>
              </thead>
              <tbody>
                <tr *ngFor="let pago of pagos">
                  <td>{{ (pago.fecha_pago || pago.fecha_creacion) | date:'dd/MM/yyyy HH:mm' }}</td>
                  <td>{{ pago.plan }}</td>
                  <td>{{ numero(pago.monto_usd) }}</td>
                  <td>{{ numero(pago.monto_bob) }}</td>
                  <td><span class="estado" [class.estado--ok]="pago.estado === 'PAGADO'">{{ pago.estado }}</span></td>
                  <td class="referencia">{{ pago.referencia_pago }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </ng-container>
    </div>
  `,
  styles: [`
    .plan-container { padding: 2rem; max-width: 1100px; margin: 0 auto; }
    h2 { color: #1a1a2e; margin-bottom: 1.25rem; }
    .subtitulo { color: #1a1a2e; margin: 1.5rem 0 0.75rem; }
    .card {
      background: white; border-radius: 10px; padding: 1.25rem 1.5rem;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); margin-bottom: 1.25rem;
    }
    .card h3 { color: #1a1a2e; margin: 0 0 0.75rem; font-size: 1.05rem; }
    .muted { color: #888; font-size: 0.85rem; }
    .etiqueta { display: block; color: #888; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
    .error { color: #c0392b; margin-bottom: 1rem; }
    .exito { color: #2e7d32; background: #e8f5e9; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem; }
    .alerta { color: #c0392b; }
    .actual-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }
    .actual-head h3 { font-size: 1.6rem; margin: 0.2rem 0; }
    .badge { padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.8rem; font-weight: 700; }
    .badge--ok { background: #e8f5e9; color: #2e7d32; }
    .badge--mal { background: #fdecea; color: #c0392b; }
    .fechas { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1rem 0; }
    .fechas div { display: flex; flex-direction: column; gap: 0.2rem; }
    .fechas strong { color: #1a1a2e; }
    .uso { display: grid; gap: 0.75rem; margin-bottom: 1rem; }
    .uso-texto { display: flex; justify-content: space-between; font-size: 0.9rem; color: #1a1a2e; margin-bottom: 0.3rem; }
    .barra { height: 8px; background: #eee; border-radius: 999px; overflow: hidden; }
    .barra-relleno { height: 100%; background: #0f3460; border-radius: 999px; }
    .barra--llena { background: #c0392b; }
    .funciones { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.35rem 1rem; }
    .funciones li { font-size: 0.9rem; color: #1a1a2e; }
    .funciones li.no { color: #aaa; }
    .funciones--chicas { grid-template-columns: 1fr; }
    .funciones--chicas li { font-size: 0.85rem; }
    .marca { display: inline-block; width: 1.2rem; font-weight: 700; color: #2e7d32; }
    .funciones li.no .marca { color: #c0392b; }
    .planes { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.25rem; }
    .plan { position: relative; display: flex; flex-direction: column; margin-bottom: 0; }
    .plan--actual { border: 2px solid #0f3460; }
    .actual-tag {
      position: absolute; top: -10px; right: 1rem; background: #0f3460; color: white;
      font-size: 0.7rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 999px;
    }
    .plan h4 { color: #1a1a2e; font-size: 1.2rem; margin: 0 0 0.5rem; }
    .precio { font-size: 1.5rem; font-weight: 700; color: #0f3460; }
    .precio span { font-size: 0.9rem; font-weight: 500; color: #888; }
    .precio-bs { color: #666; margin-bottom: 0.75rem; }
    .limites { list-style: none; padding: 0; margin: 0 0 0.75rem; font-size: 0.85rem; color: #444; }
    .limites li { padding: 0.15rem 0; }
    .nota { font-size: 0.8rem; color: #666; margin: 0.75rem 0; flex: 1; }
    .btn-bloque { width: 100%; }
    .btn-link { background: none; border: none; color: #c0392b; text-decoration: underline; cursor: pointer; }
    .pago { margin-top: 1.25rem; border: 2px solid #0f3460; }
    .tarjeta { padding: 12px; border: 1px solid #ccc; border-radius: 6px; background: white; margin: 0.4rem 0; }
    .pago-acciones { display: flex; align-items: center; gap: 1rem; margin-top: 0.75rem; flex-wrap: wrap; }
    .tabla-wrap { overflow-x: auto; }
    .tabla { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    .tabla th, .tabla td { padding: 0.6rem; text-align: left; border-bottom: 1px solid #eee; white-space: nowrap; }
    .tabla th { background: #1a1a2e; color: white; font-weight: 500; }
    .referencia { font-family: monospace; font-size: 0.75rem; color: #666; }
    .estado { font-size: 0.75rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 999px; background: #fff3e0; color: #e65100; }
    .estado--ok { background: #e8f5e9; color: #2e7d32; }
    @media (max-width: 900px) {
      .planes { grid-template-columns: 1fr; }
    }
    @media (max-width: 768px) {
      .plan-container { padding: 1rem; }
      .fechas { grid-template-columns: 1fr; }
      .funciones { grid-template-columns: 1fr; }
      .pago-acciones .btn-primary { width: 100%; }
    }
  `]
})
export class MiPlanComponent implements OnInit, OnDestroy {
  suscripcion: any = null;
  planes: any[] = [];
  pagos: any[] = [];
  cargando = true;
  error: string | null = null;
  mensajeExito: string | null = null;
  planEnPago: any = null;
  iniciando = false;
  confirmando = false;
  errorPago: string | null = null;
  funciones = FUNCIONES;
  limites = LIMITES;
  formatoFecha = formatoFecha;
  private stripe: Stripe | null = null;
  private tarjeta: StripeCardElement | null = null;
  private clientSecret: string | null = null;

  constructor(private api: ApiService, private planService: PlanService) {}

  ngOnInit(): void {
    this.cargar();
  }

  ngOnDestroy(): void {
    this.desmontarTarjeta();
  }

  cargar(): void {
    this.cargando = true;
    forkJoin({
      suscripcion: this.api.get<any>('/auth/suscripciones/actual/').pipe(catchError((err) => {
        this.error = mensajeDeError(err, 'No se pudo cargar la suscripción de tu empresa.');
        return of(null);
      })),
      planes: this.api.get<any>('/auth/planes/').pipe(catchError(() => of([]))),
      pagos: this.api.get<any>('/auth/suscripciones/pagos/').pipe(catchError(() => of([])))
    }).subscribe(({ suscripcion, planes, pagos }) => {
      this.suscripcion = suscripcion;
      this.planes = (planes?.results || planes || []).filter((p: any) => p.estado);
      this.pagos = pagos?.results || pagos || [];
      this.cargando = false;
    });
  }

  numero(valor: any): string {
    const n = Number(valor);
    return Number.isInteger(n) ? n.toLocaleString('es-BO') : n.toLocaleString('es-BO', { minimumFractionDigits: 2 });
  }

  textoPeriodo(periodo: string): string {
    return TEXTO_PERIODO[periodo] || periodo;
  }

  porcentaje(usado: number, maximo: number | null): number {
    if (maximo === null || maximo === undefined || maximo <= 0) {
      return 0;
    }
    return Math.min(100, Math.round((usado / maximo) * 100));
  }

  // Si la empresa usa más de lo que permite el plan, no puede pasarse a él (el backend también lo valida).
  motivoNoDisponible(plan: any, suscripcion: any): string | null {
    for (const limite of LIMITES) {
      const maximo = plan[limite.clave];
      const usado = suscripcion.uso[limite.uso];
      if (maximo !== null && maximo !== undefined && usado > maximo) {
        return `Tienes ${usado} ${limite.texto.toLowerCase()} y este plan permite ${maximo}.`;
      }
    }
    return null;
  }

  textoEfecto(plan: any, suscripcion: any): string {
    if (plan.id_plan === suscripcion.plan.id_plan && suscripcion.vigente) {
      return `Se suman ${plan.dias_periodo} días a tu vencimiento actual.`;
    }
    return `El nuevo periodo de ${plan.dias_periodo} días empieza hoy.`;
  }

  iniciarPago(plan: any): void {
    this.iniciando = true;
    this.errorPago = null;
    this.mensajeExito = null;
    this.api.post<any>('/auth/suscripciones/iniciar-pago/', { id_plan: plan.id_plan }).subscribe({
      next: async (data) => {
        this.clientSecret = data.client_secret;
        this.stripe = await loadStripe(data.publishable_key || environment.stripePublishableKey);
        this.iniciando = false;
        this.planEnPago = plan;
        // Se monta el campo de tarjeta cuando el bloque de pago ya está en pantalla.
        setTimeout(() => this.montarTarjeta());
      },
      error: (err) => {
        this.iniciando = false;
        this.error = mensajeDeError(err, 'No se pudo iniciar el pago.');
      }
    });
  }

  private montarTarjeta(): void {
    if (!this.stripe || !document.getElementById('tarjeta-plan')) {
      return;
    }
    this.desmontarTarjeta();
    this.tarjeta = this.stripe.elements().create('card');
    this.tarjeta.mount('#tarjeta-plan');
  }

  private desmontarTarjeta(): void {
    if (this.tarjeta) {
      this.tarjeta.destroy();
      this.tarjeta = null;
    }
  }

  async confirmarPago(): Promise<void> {
    if (!this.stripe || !this.tarjeta || !this.clientSecret || !this.planEnPago) {
      return;
    }
    this.confirmando = true;
    this.errorPago = null;
    const resultado = await this.stripe.confirmCardPayment(this.clientSecret, {
      payment_method: { card: this.tarjeta }
    });
    if (resultado.error || !resultado.paymentIntent?.id) {
      this.errorPago = resultado.error?.message || 'No se pudo confirmar el pago.';
      this.confirmando = false;
      return;
    }
    this.api.post<any>('/auth/suscripciones/confirmar-pago/', {
      referencia_pago: resultado.paymentIntent.id
    }).subscribe({
      next: (suscripcion) => {
        this.confirmando = false;
        this.mensajeExito = `Pago registrado. Tu plan ${suscripcion.plan.nombre} vence el ${formatoFecha(suscripcion.fecha_vencimiento)}.`;
        this.cancelarPago();
        this.cargar();
        // El panel actualiza el menú y los avisos con el plan nuevo.
        this.planService.cargar().subscribe();
      },
      error: (err) => {
        this.confirmando = false;
        this.errorPago = mensajeDeError(err, 'El pago se hizo pero no se pudo aplicar el plan. Intenta de nuevo.');
      }
    });
  }

  cancelarPago(): void {
    this.desmontarTarjeta();
    this.planEnPago = null;
    this.clientSecret = null;
    this.errorPago = null;
  }
}