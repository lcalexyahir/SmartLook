// web/src/app/modules/dashboard/components/comparativo-sucursales/comparativo-sucursales.component.ts
//
// NUEVO (SaaS - A.4): reporte comparativo entre sucursales (sin IA), en los
// 3 planes. Usa GET /api/bi/comparativo-sucursales/?desde=&hasta= y muestra,
// por sucursal, lo vendido en caja (POS) y por la web, las reservas y el
// stock, con un gráfico de barras hecho con CSS (sin librerías extra).
// El SUPER_ADMIN puede elegir una empresa (?empresa=<slug>) o ver todas.
import { Component, Input, OnInit } from '@angular/core';
import { ApiService } from '../../../../core/services/api.service';
import {
  EmpresaService,
  formatoFecha,
  mensajeDeError
} from '../../../empresas/services/empresa.service';

interface FilaComparativo {
  id_sucursal: number;
  sucursal: string;
  empresa: string | null;
  ventas_pos: number;
  total_pos: string;
  ordenes_web: number;
  total_web: string;
  total_vendido: string;
  reservas: number;
  stock_unidades: number;
}

type Rango = 'mes' | 'mes_anterior' | '90' | 'personalizado';

// Fecha local en formato AAAA-MM-DD (toISOString usaría UTC y podría correr el día).
function fechaLocal(fecha: Date): string {
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return `${fecha.getFullYear()}-${mes}-${dia}`;
}

@Component({
  selector: 'app-comparativo-sucursales',
  template: `
    <section class="comparativo">
      <div class="comparativo-head">
        <div>
          <h2>Comparativo entre sucursales</h2>
          <p class="muted" *ngIf="periodo">Del {{ formatoFecha(periodo.desde) }} al {{ formatoFecha(periodo.hasta) }}</p>
        </div>
        <div class="rangos">
          <button type="button" [class.activo]="rango === 'mes'" (click)="elegirRango('mes')">Este mes</button>
          <button type="button" [class.activo]="rango === 'mes_anterior'" (click)="elegirRango('mes_anterior')">Mes anterior</button>
          <button type="button" [class.activo]="rango === '90'" (click)="elegirRango('90')">Últimos 90 días</button>
        </div>
      </div>

      <div class="filtros">
        <label>
          Desde
          <input type="date" [value]="desde" [max]="hasta" (change)="cambiarFecha('desde', $event)">
        </label>
        <label>
          Hasta
          <input type="date" [value]="hasta" [min]="desde" (change)="cambiarFecha('hasta', $event)">
        </label>
        <label *ngIf="esSuperAdmin">
          Empresa
          <select [value]="empresa" (change)="cambiarEmpresa($event)">
            <option value="">Todas</option>
            <option *ngFor="let e of empresas" [value]="e.slug">{{ e.nombre }}</option>
          </select>
        </label>
      </div>

      <p *ngIf="cargando" class="muted">Cargando comparativo...</p>
      <p *ngIf="error" class="error">{{ error }}</p>

      <ng-container *ngIf="!cargando && !error">
        <p class="muted" *ngIf="filas.length === 0">No hay sucursales para mostrar.</p>

        <div class="resumen" *ngIf="filas.length > 0">
          <div class="resumen-item">
            <span class="muted">Total vendido</span>
            <strong>Bs {{ formatoMonto(totalGeneral) }}</strong>
          </div>
          <div class="resumen-item">
            <span class="muted">En caja (POS)</span>
            <strong>Bs {{ formatoMonto(totalPos) }}</strong>
          </div>
          <div class="resumen-item">
            <span class="muted">Por la web</span>
            <strong>Bs {{ formatoMonto(totalWeb) }}</strong>
          </div>
          <div class="resumen-item" *ngIf="lider">
            <span class="muted">Sucursal con más ventas</span>
            <strong>{{ lider.sucursal }}</strong>
          </div>
        </div>

        <div class="grafico" *ngIf="filas.length > 0">
          <div class="leyenda">
            <span><i class="color color--pos"></i>Caja (POS)</span>
            <span><i class="color color--web"></i>Web</span>
          </div>
          <div class="barra-fila" *ngFor="let f of filas">
            <span class="barra-nombre" [title]="f.sucursal">{{ f.sucursal }}</span>
            <div class="barra-pista">
              <div class="barra barra--pos" [style.width.%]="ancho(f.total_pos)"></div>
              <div class="barra barra--web" [style.width.%]="ancho(f.total_web)"></div>
            </div>
            <span class="barra-valor">Bs {{ formatoMonto(numero(f.total_vendido)) }}</span>
          </div>
        </div>

        <div class="tabla-wrap" *ngIf="filas.length > 0">
          <table class="tabla">
            <thead>
              <tr>
                <th>Sucursal</th>
                <th *ngIf="mostrarEmpresa">Empresa</th>
                <th class="num">Ventas POS</th>
                <th class="num">Bs POS</th>
                <th class="num">Órdenes web</th>
                <th class="num">Bs web</th>
                <th class="num">Total Bs</th>
                <th class="num">% del total</th>
                <th class="num">Reservas</th>
                <th class="num">Stock (u.)</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let f of filas">
                <td>{{ f.sucursal }}</td>
                <td *ngIf="mostrarEmpresa">{{ f.empresa || '-' }}</td>
                <td class="num">{{ f.ventas_pos }}</td>
                <td class="num">{{ formatoMonto(numero(f.total_pos)) }}</td>
                <td class="num">{{ f.ordenes_web }}</td>
                <td class="num">{{ formatoMonto(numero(f.total_web)) }}</td>
                <td class="num fuerte">{{ formatoMonto(numero(f.total_vendido)) }}</td>
                <td class="num">{{ participacion(f) }}%</td>
                <td class="num">{{ f.reservas }}</td>
                <td class="num">{{ f.stock_unidades }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </ng-container>
    </section>
  `,
  styles: [`
    .comparativo {
      margin-top: 2.5rem; padding: 1.5rem; background: #fff;
      border: 1px solid rgba(30, 26, 22, 0.14); border-radius: 6px;
    }
    .comparativo-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; }
    h2 { font-family: 'Fraunces', serif; font-weight: 500; font-size: 1.35rem; color: #1E1A16; margin: 0 0 0.25rem; }
    .muted { color: #6B6459; font-size: 0.85rem; margin: 0; }
    .error { color: #B3483D; }
    .rangos { display: flex; gap: 0.4rem; flex-wrap: wrap; }
    .rangos button {
      padding: 0.4rem 0.8rem; border: 1px solid rgba(30, 26, 22, 0.2); border-radius: 999px;
      background: #fff; color: #1E1A16; font-size: 0.8rem; cursor: pointer; font-family: inherit;
    }
    .rangos button.activo { background: #1E1A16; color: #fff; border-color: #1E1A16; }
    .filtros { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1.25rem 0; }
    .filtros label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.8rem; color: #6B6459; font-weight: 600; }
    .filtros input, .filtros select {
      padding: 0.45rem 0.6rem; border: 1px solid rgba(30, 26, 22, 0.2); border-radius: 6px;
      font-family: inherit; font-size: 0.9rem; color: #1E1A16; background: #fff;
    }
    .resumen { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
    .resumen-item { display: flex; flex-direction: column; gap: 0.25rem; padding: 0.9rem 1rem; background: #FBF8F4; border-radius: 6px; }
    .resumen-item strong { font-family: 'Fraunces', serif; font-weight: 500; font-size: 1.1rem; color: #1E1A16; overflow-wrap: anywhere; }
    .grafico { margin-bottom: 1.5rem; }
    .leyenda { display: flex; gap: 1.25rem; font-size: 0.8rem; color: #6B6459; margin-bottom: 0.75rem; }
    .color { display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 0.4rem; vertical-align: -1px; }
    .color--pos, .barra--pos { background: #1E1A16; }
    .color--web, .barra--web { background: #B98B4E; }
    .barra-fila { display: grid; grid-template-columns: 190px 1fr 120px; align-items: center; gap: 0.75rem; margin-bottom: 0.6rem; }
    .barra-nombre { font-size: 0.85rem; color: #1E1A16; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .barra-pista { display: flex; height: 18px; background: #F3EEE7; border-radius: 4px; overflow: hidden; }
    .barra { height: 100%; transition: width 0.3s ease; }
    .barra-valor { font-size: 0.85rem; font-weight: 600; color: #1E1A16; text-align: right; }
    .tabla-wrap { overflow-x: auto; }
    .tabla { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    .tabla th, .tabla td { padding: 0.6rem 0.7rem; border-bottom: 1px solid rgba(30, 26, 22, 0.1); text-align: left; white-space: nowrap; }
    .tabla th { color: #6B6459; font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.5px; }
    .tabla .num { text-align: right; }
    .tabla .fuerte { font-weight: 700; color: #1E1A16; }
    @media (max-width: 900px) {
      .resumen { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 640px) {
      .comparativo { padding: 1rem; }
      .resumen { grid-template-columns: 1fr; }
      .barra-fila { grid-template-columns: 1fr auto; grid-template-areas: 'nombre valor' 'pista pista'; row-gap: 0.3rem; }
      .barra-nombre { grid-area: nombre; }
      .barra-valor { grid-area: valor; }
      .barra-pista { grid-area: pista; }
      .filtros label { flex: 1 1 140px; }
    }
  `]
})
export class ComparativoSucursalesComponent implements OnInit {
  @Input() esSuperAdmin = false;
  filas: FilaComparativo[] = [];
  empresas: any[] = [];
  empresa = '';
  rango: Rango = 'mes';
  desde = '';
  hasta = '';
  periodo: { desde: string; hasta: string } | null = null;
  cargando = false;
  error: string | null = null;
  totalGeneral = 0;
  totalPos = 0;
  totalWeb = 0;
  lider: FilaComparativo | null = null;
  private maximo = 0;
  formatoFecha = formatoFecha;

  constructor(private api: ApiService, private empresaService: EmpresaService) {}

  ngOnInit(): void {
    if (this.esSuperAdmin) {
      this.empresaService.listar().subscribe({
        next: (data: any) => this.empresas = data.results || data,
        error: () => this.empresas = []
      });
    }
    this.elegirRango('mes');
  }

  // La columna Empresa solo tiene sentido si se ven varias empresas a la vez.
  get mostrarEmpresa(): boolean {
    return this.esSuperAdmin && !this.empresa;
  }

  elegirRango(rango: Rango): void {
    const hoy = new Date();
    let inicio: Date;
    let fin: Date = hoy;
    if (rango === 'mes_anterior') {
      inicio = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1);
      fin = new Date(hoy.getFullYear(), hoy.getMonth(), 0);
    } else if (rango === '90') {
      inicio = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate() - 89);
    } else {
      inicio = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
    }
    this.rango = rango;
    this.desde = fechaLocal(inicio);
    this.hasta = fechaLocal(fin);
    this.cargar();
  }

  cambiarFecha(campo: 'desde' | 'hasta', evento: Event): void {
    const valor = (evento.target as HTMLInputElement).value;
    if (!valor) {
      return;
    }
    this[campo] = valor;
    this.rango = 'personalizado';
    this.cargar();
  }

  cambiarEmpresa(evento: Event): void {
    this.empresa = (evento.target as HTMLSelectElement).value;
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.error = null;
    const params: any = { desde: this.desde, hasta: this.hasta };
    if (this.esSuperAdmin && this.empresa) {
      params.empresa = this.empresa;
    }
    this.api.get<any>('/bi/comparativo-sucursales/', params).subscribe({
      next: (data) => {
        this.filas = data.sucursales || [];
        this.periodo = { desde: data.desde, hasta: data.hasta };
        this.calcularTotales();
        this.cargando = false;
      },
      error: (err) => {
        this.filas = [];
        this.cargando = false;
        this.error = mensajeDeError(err, 'No se pudo cargar el comparativo entre sucursales.');
      }
    });
  }

  private calcularTotales(): void {
    this.totalPos = this.filas.reduce((s, f) => s + this.numero(f.total_pos), 0);
    this.totalWeb = this.filas.reduce((s, f) => s + this.numero(f.total_web), 0);
    this.totalGeneral = this.totalPos + this.totalWeb;
    this.maximo = this.filas.reduce((m, f) => Math.max(m, this.numero(f.total_vendido)), 0);
    // El backend ya las ordena de mayor a menor total vendido.
    this.lider = this.filas.length > 0 && this.numero(this.filas[0].total_vendido) > 0 ? this.filas[0] : null;
  }

  numero(valor: string | number | null | undefined): number {
    return Number(valor) || 0;
  }

  formatoMonto(valor: number): string {
    return valor.toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  // Ancho de cada tramo de la barra, relativo a la sucursal que más vendió.
  ancho(valor: string): number {
    return this.maximo > 0 ? (this.numero(valor) / this.maximo) * 100 : 0;
  }

  participacion(fila: FilaComparativo): string {
    if (this.totalGeneral <= 0) {
      return '0';
    }
    return ((this.numero(fila.total_vendido) / this.totalGeneral) * 100).toFixed(1);
  }
}