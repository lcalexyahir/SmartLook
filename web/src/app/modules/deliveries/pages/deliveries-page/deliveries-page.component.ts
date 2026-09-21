import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subject, timer } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { ApiService } from '../../../../core/services/api.service';
import { AuthService } from '../../../../core/auth/auth.service';

const ROLES_GESTION = ['SUPER_ADMIN', 'ADMIN_EMPRESA', 'ENCARGADO_SUCURSAL'];

@Component({
  selector: 'app-deliveries-page',
  template: `
    <div class="deliveries-container">
      <h2>{{ esGestor ? 'Entregas' : 'Mis entregas' }}</h2>
      <p class="hint">Esta pantalla se actualiza sola cada 10 segundos.</p>

      <div class="filters">
        <button type="button" *ngFor="let f of filtros"
                [class.active]="filtro === f.valor" (click)="cambiarFiltro(f.valor)">
          {{ f.texto }}
        </button>
      </div>

      <p class="msg-ok" *ngIf="mensaje">{{ mensaje }}</p>
      <p class="msg-error" *ngIf="error">{{ error }}</p>
      <div *ngIf="cargando">Cargando entregas...</div>

      <div class="empty" *ngIf="!cargando && entregas.length === 0">
        <p>No hay entregas en esta lista.</p>
      </div>

      <div class="delivery-card" *ngFor="let d of entregas; trackBy: porId">
        <div class="card-head">
          <div>
            <strong>Entrega #{{ d.id_delivery }}</strong>
            <span class="muted">Orden #{{ d.orden }} · {{ d.sucursal }}</span>
          </div>
          <span class="badge" [ngClass]="'estado-' + d.estado.toLowerCase()">{{ texto(d.estado) }}</span>
        </div>

        <div class="card-body">
          <p><strong>Cliente:</strong> {{ d.cliente }}
            <span *ngIf="d.telefono_cliente"> · Tel. {{ d.telefono_cliente }}</span></p>
          <p><strong>Dirección:</strong> {{ d.direccion }}
            <span *ngIf="d.referencia">({{ d.referencia }})</span></p>
          <p class="muted">
            {{ d.prendas }} prenda(s) · {{ d.distancia_km }} km · Pagado Bs {{ d.total_orden }}
          </p>
          <p><strong>Repartidor:</strong> {{ d.repartidor || 'Sin asignar' }}</p>
          <a class="map-link" target="_blank" rel="noopener"
             [href]="enlaceMapa(d)">Cómo llegar</a>
        </div>

        <div class="card-actions">
          <ng-container *ngIf="esGestor && (d.estado === 'PENDIENTE' || d.estado === 'EN_PREPARACION')">
            <select [(ngModel)]="seleccion[d.id_delivery]">
              <option [ngValue]="null">-- Repartidor --</option>
              <option *ngFor="let r of repartidores" [ngValue]="r.id_usuario">{{ r.nombre }}</option>
            </select>
            <button type="button" class="btn-sec" [disabled]="procesando === d.id_delivery"
                    (click)="asignar(d)">Asignar</button>
          </ng-container>

          <button type="button" class="btn-main"
                  *ngIf="esGestor && d.estado === 'PENDIENTE'"
                  [disabled]="procesando === d.id_delivery"
                  (click)="ejecutar(d, 'preparar')">Preparar pedido</button>

          <button type="button" class="btn-main"
                  *ngIf="d.estado === 'EN_PREPARACION'"
                  [disabled]="procesando === d.id_delivery || !d.id_repartidor"
                  (click)="ejecutar(d, 'en-camino')">Salir a entregar</button>

          <button type="button" class="btn-main"
                  *ngIf="d.estado === 'EN_CAMINO'"
                  [disabled]="procesando === d.id_delivery"
                  (click)="ejecutar(d, 'entregar')">Marcar entregado</button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .deliveries-container { padding: 2rem; max-width: 900px; margin: 0 auto; }
    h2 { color: #1a1a2e; margin-bottom: 0.25rem; }
    .hint { color: #999; font-size: 0.85rem; margin: 0 0 1rem; }
    .filters { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; }
    .filters button {
      padding: 0.4rem 0.9rem; border: 1px solid #d0d7e2; background: white;
      border-radius: 999px; cursor: pointer; font-size: 0.85rem; color: #1a1a2e;
    }
    .filters button.active { background: #0f3460; border-color: #0f3460; color: white; }
    .msg-ok { color: #1b7f4b; }
    .msg-error { color: #f44336; }
    .empty { text-align: center; padding: 3rem; color: #999; }
    .delivery-card {
      background: white; border-radius: 8px; padding: 1rem 1.25rem;
      margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    .card-head { display: flex; justify-content: space-between; align-items: center; }
    .muted { margin-left: 0.5rem; color: #999; font-size: 0.85rem; }
    .card-body p { margin: 0.35rem 0; color: #1a1a2e; font-size: 0.95rem; }
    .card-body .muted { margin-left: 0; }
    .map-link { font-size: 0.9rem; color: #0f3460; font-weight: 600; }
    .badge {
      padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.8rem;
      font-weight: 600; background: #eef3fb; color: #0f3460;
    }
    .badge.estado-en_preparacion { background: #fff4e0; color: #b26a00; }
    .badge.estado-en_camino { background: #e3f2fd; color: #1565c0; }
    .badge.estado-entregado { background: #e8f8f0; color: #1b7f4b; }
    .card-actions {
      display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;
      margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #eee;
    }
    .card-actions:empty { display: none; }
    .card-actions select {
      padding: 0.45rem; border: 1px solid #d0d7e2; border-radius: 6px; min-width: 180px;
    }
    .btn-main, .btn-sec {
      padding: 0.5rem 1rem; border-radius: 6px; font-weight: 600; cursor: pointer;
    }
    .btn-main { background: #0f3460; color: white; border: 1px solid #0f3460; }
    .btn-sec { background: white; color: #0f3460; border: 1px solid #0f3460; }
    button:disabled { opacity: 0.5; cursor: default; }
  `]
})
export class DeliveriesPageComponent implements OnInit, OnDestroy {
  entregas: any[] = [];
  repartidores: any[] = [];
  seleccion: { [idDelivery: number]: number | null } = {};
  cargando = true;
  error: string | null = null;
  mensaje: string | null = null;
  procesando: number | null = null;
  esGestor = false;
  filtro = '';

  filtros = [
    { valor: '', texto: 'Todas' },
    { valor: 'PENDIENTE', texto: 'Pendientes' },
    { valor: 'EN_PREPARACION', texto: 'En preparación' },
    { valor: 'EN_CAMINO', texto: 'En camino' },
    { valor: 'ENTREGADO', texto: 'Entregadas' }
  ];

  private destroy$ = new Subject<void>();

  constructor(private api: ApiService, private auth: AuthService) {}

  ngOnInit(): void {
    this.esGestor = this.auth.obtenerRoles().some((r) => ROLES_GESTION.includes(r));
    if (this.esGestor) {
      this.api.get<any>('/sales/entregas/repartidores/').subscribe({
        next: (lista) => (this.repartidores = lista),
        error: () => (this.repartidores = [])
      });
    }
    // Consulta al abrir y luego cada 10 segundos.
    timer(0, 10000).pipe(takeUntil(this.destroy$)).subscribe(() => this.cargar());
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  porId(_: number, d: any): number {
    return d.id_delivery;
  }

  cambiarFiltro(valor: string): void {
    this.filtro = valor;
    this.cargando = true;
    this.cargar();
  }

  cargar(): void {
    const params: any = { page_size: 100 };
    if (this.filtro) {
      params.estado = this.filtro;
    }
    this.api.get<any>('/sales/entregas/', params).subscribe({
      next: (data) => {
        this.cargando = false;
        this.entregas = data.results || data;
        // Deja preseleccionado el repartidor ya asignado, sin pisar lo que el usuario esté eligiendo.
        for (const d of this.entregas) {
          if (d.id_repartidor && this.seleccion[d.id_delivery] == null) {
            this.seleccion[d.id_delivery] = d.id_repartidor;
          }
        }
      },
      error: () => {
        this.cargando = false;
        this.error = 'No se pudieron cargar las entregas. Reintentando...';
      }
    });
  }

  ejecutar(d: any, accion: string, body: any = {}): void {
    this.procesando = d.id_delivery;
    this.mensaje = null;
    this.error = null;
    this.api.post<any>(`/sales/entregas/${d.id_delivery}/${accion}/`, body).subscribe({
      next: () => {
        this.procesando = null;
        this.mensaje = `Entrega #${d.id_delivery} actualizada.`;
        this.cargar();
      },
      error: (err) => {
        this.procesando = null;
        this.error = err?.error?.error || err?.error?.detail || 'No se pudo completar la acción.';
      }
    });
  }

  asignar(d: any): void {
    const id = this.seleccion[d.id_delivery];
    if (!id) {
      this.error = 'Elige un repartidor antes de asignar.';
      return;
    }
    this.ejecutar(d, 'asignar', { id_repartidor: id });
  }

  texto(estado: string): string {
    const t: { [k: string]: string } = {
      PENDIENTE: 'Pendiente',
      EN_PREPARACION: 'En preparación',
      EN_CAMINO: 'En camino',
      ENTREGADO: 'Entregado'
    };
    return t[estado] || estado;
  }

  // Enlace a Google Maps con la ruta hasta el punto de entrega (no requiere clave).
  enlaceMapa(d: any): string {
    return `https://www.google.com/maps/dir/?api=1&destination=${d.latitud},${d.longitud}`;
  }
}