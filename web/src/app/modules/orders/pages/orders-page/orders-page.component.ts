import { Component, OnDestroy, OnInit } from '@angular/core';
import { of, Subject, timer } from 'rxjs';
import { catchError, switchMap, takeUntil } from 'rxjs/operators';
import { ApiService } from '../../../../core/services/api.service';

// CU21: pasos del seguimiento de un pedido con delivery.
const PASOS_DELIVERY = [
  { clave: 'PENDIENTE', texto: 'Pedido recibido' },
  { clave: 'EN_PREPARACION', texto: 'En preparación' },
  { clave: 'EN_CAMINO', texto: 'En camino' },
  { clave: 'ENTREGADO', texto: 'Entregado' }
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
  `]
})
export class OrdersPageComponent implements OnInit, OnDestroy {
  pedidos: any[] = [];
  cargando = true;
  error: string | null = null;
  pasos = PASOS_DELIVERY;

  private destroy$ = new Subject<void>();

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    // Consulta al abrir la pantalla y luego cada 10 segundos (seguimiento en vivo).
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
      // Las órdenes PENDIENTE son pagos que nunca se completaron: no se muestran.
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
    if (o.tipo_entrega === 'DELIVERY' && o.delivery) {
      return this.pasos[this.indicePaso(o)].texto;
    }
    return o.estado === 'ENTREGADA' ? 'Entregado' : 'Pagado';
  }

  claseEstado(o: any): string {
    if (o.tipo_entrega === 'DELIVERY' && o.delivery) {
      return 'estado-' + o.delivery.estado.toLowerCase();
    }
    return 'estado-' + String(o.estado).toLowerCase();
  }
}