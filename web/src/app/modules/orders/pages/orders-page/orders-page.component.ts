// web/src/app/modules/orders/pages/orders-page/orders-page.component.ts
//
// NUEVO (devoluciones): botón "Solicitar devolución" en pedidos con
// delivery ya entregados, con modal para elegir prendas + motivo. Se
// completa sola (sin aprobación de un encargado) y muestra el mensaje
// de disculpa que devuelve el backend según el motivo.
// MODIFICADO (devoluciones): el badge ahora distingue "Devuelto" (todas
// las prendas del pedido se devolvieron) y "Entregado (con devolución
// parcial)" (solo algunas), usando los campos devuelto/tiene_devolucion
// que ahora manda OrderSerializer. El botón de devolución se oculta si
// el pedido ya se devolvió por completo.

import { Component, OnDestroy, OnInit } from '@angular/core';
import { of, Subject, timer } from 'rxjs';
import { catchError, switchMap, takeUntil } from 'rxjs/operators';
import { ApiService } from '../../../../core/services/api.service';

const PASOS_DELIVERY = [
  { clave: 'PENDIENTE', texto: 'Pedido recibido' },
  { clave: 'EN_PREPARACION', texto: 'En preparación' },
  { clave: 'EN_CAMINO', texto: 'En camino' },
  { clave: 'ENTREGADO', texto: 'Entregado' }
];

const MOTIVOS_DEVOLUCION = [
  { value: 'TALLA_INCORRECTA', label: 'Talla incorrecta' },
  { value: 'COLOR_INCORRECTO', label: 'Color incorrecto' },
  { value: 'PRODUCTO_DANADO', label: 'Producto dañado/defectuoso' },
  { value: 'OTRO', label: 'Otro' }
];

@Component({
  selector: 'app-orders-page',
  template: `
    <div class="orders-container">
      <h2>Mis pedidos</h2>
      <p class="hint">Esta pantalla se actualiza sola cada 10 segundos.</p>

      <div *ngIf="cargando">Cargando pedidos...</div>
      <p class="error" *ngIf="error">{{ error }}</p>

      <div class="empty" *ngIf="!cargando && !error && pedidos.length === 0">
        <p>Todavía no tienes pedidos.</p>
        <a routerLink="/catalog" class="btn btn-accent">Ir al catálogo</a>
      </div>

      <div class="order-card" *ngFor="let o of pedidos">
        <div class="order-head">
          <div>
            <strong>Pedido #{{ o.id_orden }}</strong>
            <span class="order-date">{{ o.fecha_creacion | date:'dd/MM/yyyy HH:mm' }}</span>
          </div>
          <span class="badge" [ngClass]="claseEstado(o)">{{ textoEstado(o) }}</span>
        </div>

        <ul class="order-items">
          <li *ngFor="let i of o.items">
            <span>{{ i.cantidad }} x {{ i.variante }}</span>
            <span>Bs {{ i.subtotal }}</span>
          </li>
        </ul>

        <div class="order-total">
          <span *ngIf="o.tipo_entrega === 'DELIVERY'">Envío: Bs {{ o.costo_envio }}</span>
          <strong>Total: Bs {{ o.total }}</strong>
        </div>

        <div class="order-delivery" *ngIf="o.tipo_entrega === 'DELIVERY' && o.delivery">
          <p>
            Entrega en: {{ o.delivery.direccion }}
            <span *ngIf="o.delivery.referencia">({{ o.delivery.referencia }})</span>
          </p>
          <p *ngIf="o.delivery.repartidor">Repartidor: {{ o.delivery.repartidor }}</p>
          <ol class="timeline">
            <li *ngFor="let p of pasos; let idx = index"
                [class.done]="idx <= indicePaso(o)"
                [class.current]="idx === indicePaso(o)">
              <span class="dot"></span>{{ p.texto }}
            </li>
          </ol>
        </div>

        <p class="order-pickup" *ngIf="o.tipo_entrega !== 'DELIVERY'">
          Retiro en sucursal: {{ o.sucursal }}
        </p>

        <p class="order-devolucion-nota" *ngIf="o.tiene_devolucion">
          Este pedido tiene una devolución registrada.
        </p>

        <div class="order-actions" *ngIf="puedeDevolver(o)">
          <button class="btn btn-link" (click)="abrirDevolucion(o)">Solicitar devolución</button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" *ngIf="mostrandoDevolucion" (click)="cerrarDevolucion()">
      <div class="modal" (click)="$event.stopPropagation()">
        <h3>Devolver prendas del Pedido #{{ mostrandoDevolucion.id_orden }}</h3>

        <div class="mensajes-exito" *ngIf="mensajesDevolucion">
          <p *ngFor="let m of mensajesDevolucion">{{ m }}</p>
          <button class="btn btn-primary" (click)="cerrarDevolucion()">Cerrar</button>
        </div>

        <div *ngIf="!mensajesDevolucion">
          <p class="error" *ngIf="errorDevolucion">{{ errorDevolucion }}</p>

          <div class="devolucion-item" *ngFor="let item of itemsDevolucion">
            <label class="checkbox-row">
              <input type="checkbox" [(ngModel)]="item.incluir">
              {{ item.variante }} (compraste {{ item.cantidadMaxima }})
            </label>

            <div class="devolucion-fields" *ngIf="item.incluir">
              <div class="form-group">
                <label>Cantidad a devolver</label>
                <input type="number" min="1" [max]="item.cantidadMaxima" [(ngModel)]="item.cantidad">
              </div>
              <div class="form-group">
                <label>Motivo</label>
                <select [(ngModel)]="item.motivo">
                  <option *ngFor="let m of motivos" [value]="m.value">{{ m.label }}</option>
                </select>
              </div>
            </div>
          </div>

          <div class="modal-actions">
            <button class="btn" (click)="cerrarDevolucion()">Cancelar</button>
            <button class="btn btn-primary" [disabled]="enviandoDevolucion" (click)="enviarDevolucion()">
              {{ enviandoDevolucion ? 'Enviando...' : 'Confirmar devolución' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .orders-container { padding: 2rem; max-width: 800px; margin: 0 auto; }
    h2 { color: #1a1a2e; margin-bottom: 0.25rem; }
    .hint { color: #999; font-size: 0.85rem; margin: 0 0 1.5rem; }
    .error { color: #f44336; }
    .empty { text-align: center; padding: 3rem; color: #999; }
    .empty .btn { margin-top: 1rem; display: inline-block; }
    .order-card {
      background: white; border-radius: 8px; padding: 1rem 1.25rem;
      margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    .order-head { display: flex; justify-content: space-between; align-items: center; }
    .order-date { margin-left: 0.75rem; font-size: 0.85rem; color: #999; }
    .badge {
      padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.8rem;
      font-weight: 600; background: #eef3fb; color: #0f3460;
    }
    .badge.estado-entregado, .badge.estado-entregada { background: #e8f8f0; color: #1b7f4b; }
    .badge.estado-cancelada { background: #fdecea; color: #c62828; }
    .badge.estado-devuelto { background: #f3e8fd; color: #6a1b9a; }
    .badge.estado-devolucion-parcial { background: #fff3e0; color: #e65100; }
    .order-items { list-style: none; padding: 0; margin: 0.75rem 0; }
    .order-items li {
      display: flex; justify-content: space-between; padding: 0.25rem 0;
      color: #1a1a2e; font-size: 0.95rem;
    }
    .order-total {
      display: flex; justify-content: space-between; align-items: center;
      border-top: 1px solid #eee; padding-top: 0.5rem; color: #1a1a2e;
    }
    .order-delivery { margin-top: 0.75rem; font-size: 0.9rem; color: #444; }
    .order-delivery p { margin: 0.25rem 0; }
    .order-pickup { margin: 0.75rem 0 0; font-size: 0.9rem; color: #444; }
    .order-devolucion-nota { margin: 0.75rem 0 0; font-size: 0.85rem; color: #6a1b9a; }
    .timeline { display: flex; list-style: none; padding: 0; margin: 1rem 0 0; }
    .timeline li {
      flex: 1; text-align: center; font-size: 0.8rem; color: #aaa; position: relative;
    }
    .timeline li::before {
      content: ''; position: absolute; top: 6px; left: -50%;
      width: 100%; height: 2px; background: #ddd;
    }
    .timeline li:first-child::before { display: none; }
    .timeline li.done { color: #0f3460; }
    .timeline li.done::before { background: #0f3460; }
    .timeline li.current { font-weight: 700; }
    .timeline .dot {
      display: block; width: 14px; height: 14px; border-radius: 50%;
      background: #ddd; margin: 0 auto 6px; position: relative; z-index: 1;
    }
    .timeline li.done .dot { background: #0f3460; }
    .order-actions { margin-top: 0.75rem; text-align: right; }
    .btn-link {
      background: none; border: none; color: #0f3460; font-weight: 600;
      text-decoration: underline; cursor: pointer; padding: 0;
    }
    .modal-overlay {
      position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5);
      display: flex; align-items: center; justify-content: center; z-index: 1000;
    }
    .modal {
      background: white; border-radius: 10px; padding: 1.5rem;
      width: 90%; max-width: 480px; max-height: 85vh; overflow-y: auto;
    }
    .modal h3 { margin-top: 0; color: #1a1a2e; }
    .devolucion-item { border-top: 1px solid #eee; padding: 0.75rem 0; }
    .checkbox-row { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; }
    .devolucion-fields { margin-top: 0.5rem; padding-left: 1.5rem; display: flex; gap: 1rem; }
    .form-group { flex: 1; }
    .form-group label { display: block; font-size: 0.8rem; color: #666; margin-bottom: 0.25rem; }
    .form-group input, .form-group select {
      width: 100%; padding: 0.4rem; border-radius: 6px; border: 1px solid #ddd;
    }
    .modal-actions {
      display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;
    }
    .btn { padding: 0.5rem 1rem; border-radius: 6px; border: 1px solid #ddd; background: white; cursor: pointer; }
    .btn-primary { background: #0f3460; color: white; border-color: #0f3460; }
    .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
    .mensajes-exito p { color: #1b7f4b; margin: 0.5rem 0; }
  `]
})
export class OrdersPageComponent implements OnInit, OnDestroy {
  pedidos: any[] = [];
  cargando = true;
  error: string | null = null;
  pasos = PASOS_DELIVERY;
  motivos = MOTIVOS_DEVOLUCION;

  mostrandoDevolucion: any = null;
  itemsDevolucion: any[] = [];
  enviandoDevolucion = false;
  errorDevolucion: string | null = null;
  mensajesDevolucion: string[] | null = null;

  private destroy$ = new Subject<void>();

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    timer(0, 10000).pipe(
      switchMap(() =>
        this.api.get<any>('/sales/ordenes/').pipe(catchError(() => of(null)))
      ),
      takeUntil(this.destroy$)
    ).subscribe((data) => {
      this.cargando = false;
      if (data === null) {
        this.error = 'No se pudieron cargar tus pedidos. Reintentando...';
        return;
      }
      this.error = null;
      const lista: any[] = data.results || data;
      this.pedidos = lista.filter((o) => o.estado !== 'PENDIENTE');
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  indicePaso(o: any): number {
    const estado = o.delivery?.estado;
    const i = this.pasos.findIndex((p) => p.clave === estado);
    return i < 0 ? 0 : i;
  }

  textoEstado(o: any): string {
    if (o.estado === 'CANCELADA') {
      return 'Cancelado';
    }
    if (o.devuelto) {
      return 'Devuelto';
    }
    if (o.tiene_devolucion) {
      return 'Entregado (devolución parcial)';
    }
    if (o.tipo_entrega === 'DELIVERY' && o.delivery) {
      return this.pasos[this.indicePaso(o)].texto;
    }
    return o.estado === 'ENTREGADA' ? 'Entregado' : 'Pagado';
  }

  claseEstado(o: any): string {
    if (o.devuelto) {
      return 'estado-devuelto';
    }
    if (o.tiene_devolucion) {
      return 'estado-devolucion-parcial';
    }
    if (o.tipo_entrega === 'DELIVERY' && o.delivery) {
      return 'estado-' + o.delivery.estado.toLowerCase();
    }
    return 'estado-' + String(o.estado).toLowerCase();
  }

  puedeDevolver(o: any): boolean {
    return o.tipo_entrega === 'DELIVERY' && o.estado === 'ENTREGADA' && !o.devuelto;
  }

  abrirDevolucion(o: any): void {
    this.mostrandoDevolucion = o;
    this.errorDevolucion = null;
    this.mensajesDevolucion = null;
    this.itemsDevolucion = o.items.map((i: any) => ({
      id_orden_item: i.id_item,
      variante: i.variante,
      cantidadMaxima: i.cantidad,
      cantidad: i.cantidad,
      motivo: 'TALLA_INCORRECTA',
      incluir: false
    }));
  }

  cerrarDevolucion(): void {
    this.mostrandoDevolucion = null;
  }

  enviarDevolucion(): void {
    if (!this.mostrandoDevolucion) return;

    const seleccionados = this.itemsDevolucion.filter((i) => i.incluir);
    if (seleccionados.length === 0) {
      this.errorDevolucion = 'Selecciona al menos una prenda a devolver.';
      return;
    }

    this.enviandoDevolucion = true;
    this.errorDevolucion = null;

    const payload = {
      id_orden: this.mostrandoDevolucion.id_orden,
      items: seleccionados.map((i) => ({
        id_orden_item: i.id_orden_item,
        cantidad: i.cantidad,
        motivo: i.motivo
      }))
    };

    this.api.post<any>('/sales/devoluciones/solicitar/', payload).subscribe({
      next: (data: any) => {
        this.enviandoDevolucion = false;
        this.mensajesDevolucion = data.mensajes;
      },
      error: (err) => {
        this.enviandoDevolucion = false;
        this.errorDevolucion = err.error?.error || 'No se pudo registrar la devolución.';
      }
    });
  }
}