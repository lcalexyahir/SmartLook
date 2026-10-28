// web/src/app/modules/profile/pages/profile-page/profile-page.component.ts
//
// NUEVO: perfil del cliente. Reemplaza al placeholder "Próximamente".
// - Datos: nombres, apellidos, teléfono y dirección se pueden editar; el
//   correo no, porque es el usuario de inicio de sesión.
// - Historial de compras: pedidos del cliente en todas las tiendas.
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../../../core/services/api.service';

const PATRON_TELEFONO = /^(\+?591)?\s?[67]\d{7}$/;

@Component({
  selector: 'app-profile-page',
  template: `
    <div class="perfil-container">
      <h2>Mi perfil</h2>
      <p *ngIf="cargando">Cargando perfil...</p>
      <p class="error" *ngIf="errorCarga">{{ errorCarga }}</p>
      <div class="perfil-grid" *ngIf="perfil">
        <section class="card">
          <div class="cabecera">
            <div class="avatar">{{ iniciales }}</div>
            <div class="cabecera-info">
              <h3>{{ perfil.nombres }} {{ perfil.apellidos }}</h3>
              <p>{{ perfil.correo }}</p>
              <p class="muted">Cliente desde {{ perfil.fecha_registro | date:'dd/MM/yyyy' }}</p>
            </div>
          </div>
          <form [formGroup]="form" (ngSubmit)="guardar()">
            <div class="form-row">
              <div class="form-group">
                <label for="nombres">Nombres</label>
                <input id="nombres" type="text" formControlName="nombres" maxlength="100">
              </div>
              <div class="form-group">
                <label for="apellidos">Apellidos</label>
                <input id="apellidos" type="text" formControlName="apellidos" maxlength="100">
              </div>
            </div>
            <div class="form-group">
              <label for="correo">Correo</label>
              <input id="correo" type="email" [value]="perfil.correo" disabled>
              <small class="ayuda">El correo es tu usuario de inicio de sesión y no se puede cambiar.</small>
            </div>
            <div class="form-group">
              <label for="telefono">Teléfono</label>
              <input id="telefono" type="text" formControlName="telefono" maxlength="20">
              <small class="campo-error" *ngIf="form.get('telefono')?.invalid && form.get('telefono')?.touched">
                Debe tener 8 dígitos y comenzar con 6 o 7.
              </small>
            </div>
            <div class="form-group" *ngIf="perfil.es_cliente">
              <label for="direccion">Dirección</label>
              <input id="direccion" type="text" formControlName="direccion" maxlength="250">
            </div>
            <p class="ok" *ngIf="mensajeOk">{{ mensajeOk }}</p>
            <p class="error" *ngIf="errorGuardar">{{ errorGuardar }}</p>
            <button type="submit" class="btn btn-primary" [disabled]="form.invalid || form.pristine || guardando">
              {{ guardando ? 'Guardando...' : 'Guardar cambios' }}
            </button>
          </form>
        </section>
        <section class="card" *ngIf="perfil.es_cliente">
          <div class="historial-head">
            <h3>Historial de compras</h3>
            <a routerLink="/orders">Ver mis pedidos</a>
          </div>
          <p class="resumen" *ngIf="compras.length > 0">
            {{ compras.length }} compra(s) · Total Bs {{ totalGastado | number:'1.2-2' }}
          </p>
          <p *ngIf="cargandoCompras">Cargando compras...</p>
          <p class="muted" *ngIf="!cargandoCompras && compras.length === 0">Todavía no tienes compras.</p>
          <ul class="compras">
            <li *ngFor="let o of compras">
              <div class="compra-top">
                <strong>Pedido #{{ o.id_orden }}</strong>
                <span class="estado">{{ textoEstado(o) }}</span>
              </div>
              <div class="compra-detalle">
                <span>{{ o.fecha_creacion | date:'dd/MM/yyyy HH:mm' }}</span>
                <span *ngIf="o.empresa_nombre">Tienda: {{ o.empresa_nombre }}</span>
                <span>{{ prendas(o) }} prenda(s)</span>
                <span class="monto">Bs {{ o.total }}</span>
              </div>
            </li>
          </ul>
        </section>
      </div>
    </div>
  `,
  styles: [`
    .perfil-container { padding: 2rem; max-width: 1100px; margin: 0 auto; }
    h2 { color: #1a1a2e; margin-bottom: 1.25rem; }
    .perfil-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; align-items: start; }
    .card { background: white; border-radius: 10px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); }
    .cabecera { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem; }
    .avatar {
      width: 72px; height: 72px; flex-shrink: 0; border-radius: 50%; background: #1a1a2e; color: white;
      display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.4rem;
    }
    .cabecera-info { min-width: 0; }
    .cabecera-info h3 { color: #1a1a2e; margin: 0 0 0.2rem; }
    .cabecera-info p { word-break: break-word; }
    .muted { color: #888; font-size: 0.85rem; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .form-group { margin-bottom: 1rem; }
    .form-group label { display: block; margin-bottom: 0.35rem; font-weight: 600; font-size: 0.9rem; }
    .form-group input { width: 100%; padding: 0.6rem; border-radius: 6px; border: 1px solid #ccc; font-size: 0.95rem; }
    .form-group input:disabled { background: #f3f3f3; color: #777; }
    .ayuda { display: block; color: #888; font-size: 0.8rem; margin-top: 0.25rem; }
    .campo-error { display: block; color: #c0392b; font-size: 0.8rem; margin-top: 0.25rem; }
    .ok { color: #2e7d32; margin-bottom: 0.75rem; }
    .error { color: #c0392b; margin-bottom: 0.75rem; }
    .historial-head { display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; }
    .historial-head h3 { color: #1a1a2e; margin: 0; }
    .historial-head a { color: #0f3460; font-size: 0.9rem; }
    .resumen { color: #0f3460; font-weight: 600; margin-bottom: 0.75rem; }
    .compras { list-style: none; padding: 0; margin: 0; }
    .compras li { border-top: 1px solid #eee; padding: 0.75rem 0; }
    .compra-top { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }
    .estado {
      font-size: 0.75rem; font-weight: 600; padding: 0.15rem 0.6rem; border-radius: 999px;
      background: #eef3fb; color: #0f3460;
    }
    .compra-detalle {
      display: flex; flex-wrap: wrap; gap: 0.25rem 1rem; margin-top: 0.35rem;
      font-size: 0.85rem; color: #666;
    }
    .compra-detalle .monto { color: #1a1a2e; font-weight: 600; margin-left: auto; }
    @media (max-width: 900px) {
      .perfil-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 768px) {
      .perfil-container { padding: 1rem; }
      .form-row { grid-template-columns: 1fr; gap: 0; }
      .btn { width: 100%; }
    }
  `]
})
export class ProfilePageComponent implements OnInit {
  perfil: any = null;
  compras: any[] = [];
  form!: FormGroup;
  cargando = true;
  cargandoCompras = false;
  guardando = false;
  errorCarga: string | null = null;
  errorGuardar: string | null = null;
  mensajeOk: string | null = null;

  constructor(private api: ApiService, private fb: FormBuilder) {}

  ngOnInit(): void {
    this.form = this.fb.group({
      nombres: ['', Validators.required],
      apellidos: ['', Validators.required],
      telefono: ['', Validators.pattern(PATRON_TELEFONO)],
      direccion: ['']
    });
    this.api.get<any>('/auth/perfil/').subscribe({
      next: (perfil) => {
        this.cargando = false;
        this.mostrarPerfil(perfil);
        if (perfil.es_cliente) {
          this.cargarCompras();
        }
      },
      error: () => {
        this.cargando = false;
        this.errorCarga = 'No se pudo cargar tu perfil.';
      }
    });
  }

  get iniciales(): string {
    const n = this.perfil?.nombres?.[0] || '';
    const a = this.perfil?.apellidos?.[0] || '';
    return (n + a).toUpperCase();
  }

  // Suma de lo comprado, sin contar pedidos cancelados.
  get totalGastado(): number {
    return this.compras
      .filter(o => o.estado !== 'CANCELADA')
      .reduce((suma, o) => suma + (Number(o.total) || 0), 0);
  }

  private mostrarPerfil(perfil: any): void {
    this.perfil = perfil;
    this.form.reset({
      nombres: perfil.nombres || '',
      apellidos: perfil.apellidos || '',
      telefono: perfil.telefono || '',
      direccion: perfil.direccion || ''
    });
  }

  private cargarCompras(): void {
    this.cargandoCompras = true;
    this.api.get<any>('/sales/ordenes/', { page_size: 100 }).subscribe({
      next: (data) => {
        const lista: any[] = data.results || data;
        // Los pedidos PENDIENTE son pagos que no se completaron.
        this.compras = lista.filter(o => o.estado !== 'PENDIENTE');
        this.cargandoCompras = false;
      },
      error: () => {
        this.compras = [];
        this.cargandoCompras = false;
      }
    });
  }

  prendas(orden: any): number {
    return (orden.items || []).reduce((suma: number, i: any) => suma + (Number(i.cantidad) || 0), 0);
  }

  textoEstado(orden: any): string {
    if (orden.estado === 'CANCELADA') {
      return 'Cancelado';
    }
    if (orden.devuelto) {
      return 'Devuelto';
    }
    return orden.estado === 'ENTREGADA' ? 'Entregado' : 'Pagado';
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const valores = this.form.value;
    const datos: any = {
      nombres: valores.nombres,
      apellidos: valores.apellidos,
      telefono: valores.telefono || null
    };
    if (this.perfil?.es_cliente) {
      datos.direccion = valores.direccion || null;
    }
    this.guardando = true;
    this.errorGuardar = null;
    this.mensajeOk = null;
    this.api.patch<any>('/auth/perfil/', datos).subscribe({
      next: (perfil) => {
        this.guardando = false;
        this.mostrarPerfil(perfil);
        this.actualizarSesion(perfil);
        this.mensajeOk = 'Datos guardados.';
      },
      error: (err) => {
        this.guardando = false;
        const e = err?.error || {};
        this.errorGuardar = e.telefono?.[0] || e.nombres?.[0] || e.apellidos?.[0]
          || e.detail || 'No se pudieron guardar los cambios.';
      }
    });
  }

  // Mantiene el nombre de la barra superior al día con lo que se guardó.
  private actualizarSesion(perfil: any): void {
    try {
      const guardado = JSON.parse(localStorage.getItem('usuario') || 'null');
      if (guardado) {
        guardado.nombres = perfil.nombres;
        guardado.apellidos = perfil.apellidos;
        guardado.telefono = perfil.telefono;
        localStorage.setItem('usuario', JSON.stringify(guardado));
      }
    } catch {
      // Si el dato guardado no es válido, se actualizará en el próximo inicio de sesión.
    }
  }
}