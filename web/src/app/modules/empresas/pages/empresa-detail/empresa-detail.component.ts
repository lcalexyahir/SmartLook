// web/src/app/modules/empresas/pages/empresa-detail/empresa-detail.component.ts
//
// NUEVO (SaaS): perfil de una empresa con su logo, datos, administrador,
// suscripción (plan, vencimiento y días restantes) y sus sucursales, con el
// formulario para registrar una sucursal nueva dentro de la empresa.
// El SUPER_ADMIN además puede suspender o reactivar la empresa.
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { AuthService } from '../../../../core/auth/auth.service';
import {
  Empresa,
  EmpresaService,
  formatoFecha,
  iniciales,
  mensajeDeError
} from '../../services/empresa.service';

@Component({
  selector: 'app-empresa-detail',
  template: `
    <div class="detalle-container">
      <a class="volver" routerLink="/empresas" *ngIf="esSuperAdmin">← Empresas</a>
      <p *ngIf="cargando">Cargando empresa...</p>
      <p class="error" *ngIf="error">{{ error }}</p>
      <ng-container *ngIf="empresa as e">
        <section class="perfil card">
          <div class="avatar">
            <img *ngIf="e.logo && !logoRoto" [src]="e.logo" [alt]="'Logo de ' + e.nombre" (error)="logoRoto = true">
            <span *ngIf="!e.logo || logoRoto">{{ iniciales(e.nombre) }}</span>
          </div>
          <div class="perfil-info">
            <div class="titulo">
              <h2>{{ e.nombre }}</h2>
              <span class="badge" [class.activa]="e.estado === 'ACTIVA'">{{ e.estado }}</span>
            </div>
            <p class="muted">Registrada el {{ e.fecha_creacion | date:'dd/MM/yyyy' }}</p>
          </div>
          <div class="perfil-acciones">
            <a class="btn btn-primary" [routerLink]="['/empresas', e.id_empresa, 'editar']">Editar</a>
            <button *ngIf="esSuperAdmin" type="button" class="btn"
                    [class.btn-danger]="e.estado === 'ACTIVA'" [class.btn-success]="e.estado !== 'ACTIVA'"
                    [disabled]="cambiandoEstado" (click)="cambiarEstado(e)">
              {{ e.estado === 'ACTIVA' ? 'Suspender' : 'Reactivar' }}
            </button>
          </div>
        </section>
        <div class="tarjetas">
          <section class="card">
            <h3>Datos</h3>
            <dl>
              <dt>NIT</dt><dd>{{ e.nit || '-' }}</dd>
              <dt>Correo</dt><dd>{{ e.correo_contacto || '-' }}</dd>
              <dt>Teléfono</dt><dd>{{ e.telefono || '-' }}</dd>
            </dl>
          </section>
          <section class="card">
            <h3>Administrador</h3>
            <dl *ngIf="e.administrador as a; else sinAdmin">
              <dt>Nombre</dt><dd>{{ a.nombre }}</dd>
              <dt>Correo</dt><dd>{{ a.correo }}</dd>
              <dt>Teléfono</dt><dd>{{ a.telefono || '-' }}</dd>
            </dl>
            <ng-template #sinAdmin><p class="muted">Sin administrador asignado.</p></ng-template>
          </section>
          <section class="card">
            <h3>Suscripción</h3>
            <dl *ngIf="e.suscripcion as s; else sinPlan">
              <dt>Plan</dt><dd>{{ s.plan_nombre }}</dd>
              <dt>Inicio</dt><dd>{{ formatoFecha(s.fecha_inicio) }}</dd>
              <dt>Vencimiento</dt><dd>{{ formatoFecha(s.fecha_vencimiento) }}</dd>
              <dt>Tiempo restante</dt>
              <dd [class.alerta]="s.dias_restantes <= 7">
                {{ s.dias_restantes < 0 ? 'Vencida' : s.dias_restantes + ' días' }}
              </dd>
              <dt>Estado</dt><dd>{{ s.estado }}</dd>
            </dl>
            <ng-template #sinPlan><p class="muted">Sin suscripción.</p></ng-template>
          </section>
        </div>
        <section class="card">
          <div class="seccion-head">
            <h3>Sucursales ({{ sucursales.length }})</h3>
            <button type="button" class="btn btn-primary" (click)="alternarFormulario(e)">
              {{ mostrarFormulario ? 'Cancelar' : 'Registrar sucursal' }}
            </button>
          </div>
          <form *ngIf="mostrarFormulario" class="sucursal-form" [formGroup]="sucursalForm" (ngSubmit)="registrarSucursal(e)">
            <div class="form-row">
              <div class="form-group">
                <label for="suc_nombre">Nombre *</label>
                <input id="suc_nombre" type="text" formControlName="nombre" maxlength="150">
              </div>
              <div class="form-group">
                <label for="suc_ciudad">Ciudad *</label>
                <select id="suc_ciudad" formControlName="id_ciudad">
                  <option [ngValue]="null">-- Selecciona una ciudad --</option>
                  <option *ngFor="let c of ciudades" [ngValue]="c.id_ciudad">{{ c.nombre }}</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label for="suc_direccion">Dirección *</label>
              <input id="suc_direccion" type="text" formControlName="direccion" maxlength="250">
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="suc_telefono">Teléfono</label>
                <input id="suc_telefono" type="text" formControlName="telefono" maxlength="20">
              </div>
              <div class="form-group">
                <label for="suc_fecha">Fecha de apertura</label>
                <input id="suc_fecha" type="date" formControlName="fecha_apertura">
              </div>
            </div>
            <p class="error" *ngIf="errorSucursal">{{ errorSucursal }}</p>
            <button type="submit" class="btn btn-success" [disabled]="sucursalForm.invalid || guardandoSucursal">
              {{ guardandoSucursal ? 'Guardando...' : 'Guardar sucursal' }}
            </button>
          </form>
          <div class="tabla-wrap">
            <table class="tabla">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Ciudad</th>
                  <th>Dirección</th>
                  <th>Teléfono</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                <tr *ngFor="let s of sucursales">
                  <td>{{ s.nombre }}</td>
                  <td>{{ s.ciudad?.nombre }}</td>
                  <td>{{ s.direccion }}</td>
                  <td>{{ s.telefono || '-' }}</td>
                  <td><span class="badge" [class.activa]="s.estado === 'ACTIVA'">{{ s.estado }}</span></td>
                </tr>
                <tr *ngIf="sucursales.length === 0">
                  <td colspan="5" class="muted">La empresa todavía no tiene sucursales.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </ng-container>
    </div>
  `,
  styles: [`
    .detalle-container { padding: 2rem; max-width: 1100px; margin: 0 auto; }
    .volver { color: #0f3460; text-decoration: none; font-size: 0.9rem; display: inline-block; margin-bottom: 0.75rem; }
    .card {
      background: white; border-radius: 10px; padding: 1.25rem 1.5rem;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); margin-bottom: 1.25rem;
    }
    .card h3 { color: #1a1a2e; font-size: 1rem; margin-bottom: 0.75rem; }
    .perfil { display: flex; align-items: center; gap: 1.25rem; flex-wrap: wrap; }
    .avatar {
      width: 96px; height: 96px; flex-shrink: 0; border-radius: 50%; overflow: hidden;
      background: #1a1a2e; color: white; display: flex; align-items: center; justify-content: center;
      font-weight: 700; font-size: 1.8rem; border: 3px solid #e0e0e0;
    }
    .avatar img { width: 100%; height: 100%; object-fit: cover; background: white; }
    .perfil-info { flex: 1; min-width: 200px; }
    .titulo { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
    .titulo h2 { color: #1a1a2e; margin: 0; }
    .perfil-acciones { display: flex; gap: 0.5rem; flex-wrap: wrap; }
    .perfil-acciones .btn { text-decoration: none; display: inline-block; }
    .muted { color: #888; font-size: 0.9rem; }
    .tarjetas { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.25rem; }
    .tarjetas .card { margin-bottom: 0; }
    .tarjetas { margin-bottom: 1.25rem; }
    dl { display: grid; grid-template-columns: auto 1fr; gap: 0.4rem 1rem; font-size: 0.9rem; }
    dt { color: #888; }
    dd { color: #1a1a2e; word-break: break-word; }
    .alerta { color: #c0392b; font-weight: 600; }
    .badge {
      padding: 0.15rem 0.6rem; border-radius: 20px; font-size: 0.75rem;
      font-weight: 600; background: #fdecea; color: #c0392b;
    }
    .badge.activa { background: #e8f5e9; color: #2e7d32; }
    .seccion-head {
      display: flex; justify-content: space-between; align-items: center;
      gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1rem;
    }
    .seccion-head h3 { margin: 0; }
    .sucursal-form { border: 1px solid #eee; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .form-group { margin-bottom: 1rem; }
    .form-group label { display: block; margin-bottom: 0.35rem; font-weight: 600; font-size: 0.9rem; }
    .form-group input, .form-group select {
      width: 100%; padding: 0.6rem; border-radius: 6px; border: 1px solid #ccc; font-size: 0.95rem;
    }
    .error { color: #c0392b; margin-bottom: 1rem; }
    .tabla-wrap { overflow-x: auto; }
    .tabla { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    .tabla th, .tabla td { padding: 0.7rem; text-align: left; border-bottom: 1px solid #eee; white-space: nowrap; }
    .tabla th { background: #1a1a2e; color: white; font-weight: 500; }
    @media (max-width: 900px) {
      .tarjetas { grid-template-columns: 1fr; }
    }
    @media (max-width: 768px) {
      .detalle-container { padding: 1rem; }
      .perfil { flex-direction: column; text-align: center; }
      .titulo { justify-content: center; }
      .perfil-acciones { justify-content: center; }
      .form-row { grid-template-columns: 1fr; gap: 0; }
      .sucursal-form .btn { width: 100%; }
    }
  `]
})
export class EmpresaDetailComponent implements OnInit {
  empresa: Empresa | null = null;
  sucursales: any[] = [];
  ciudades: any[] = [];
  esSuperAdmin = false;
  cargando = true;
  error: string | null = null;
  logoRoto = false;
  cambiandoEstado = false;
  mostrarFormulario = false;
  guardandoSucursal = false;
  errorSucursal: string | null = null;
  sucursalForm!: FormGroup;
  iniciales = iniciales;
  formatoFecha = formatoFecha;

  constructor(
    private route: ActivatedRoute,
    private fb: FormBuilder,
    private empresaService: EmpresaService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.esSuperAdmin = this.authService.obtenerRoles().includes('SUPER_ADMIN');
    this.sucursalForm = this.fb.group({
      nombre: ['', Validators.required],
      id_ciudad: [null, Validators.required],
      direccion: ['', Validators.required],
      telefono: [''],
      fecha_apertura: ['']
    });
    // Se escucha el parámetro por si se navega de una empresa a otra sin salir de la página.
    this.route.paramMap.subscribe(params => {
      this.cargarEmpresa(Number(params.get('id')));
    });
  }

  cargarEmpresa(id: number): void {
    this.cargando = true;
    this.error = null;
    this.logoRoto = false;
    this.empresaService.obtener(id).subscribe({
      next: (empresa) => {
        this.empresa = empresa;
        this.cargando = false;
        this.cargarSucursales(empresa);
      },
      error: (err) => {
        this.empresa = null;
        this.cargando = false;
        this.error = mensajeDeError(err, 'No se encontró la empresa.');
      }
    });
  }

  cargarSucursales(empresa: Empresa): void {
    this.empresaService.sucursales(empresa.slug).subscribe({
      next: (data: any) => this.sucursales = data.results || data,
      error: () => this.sucursales = []
    });
  }

  cambiarEstado(empresa: Empresa): void {
    const nuevo = empresa.estado === 'ACTIVA' ? 'SUSPENDIDA' : 'ACTIVA';
    const pregunta = nuevo === 'SUSPENDIDA'
      ? `¿Suspender ${empresa.nombre}? Su personal no podrá iniciar sesión y sus productos dejarán de verse en el catálogo.`
      : `¿Reactivar ${empresa.nombre}?`;
    if (!confirm(pregunta)) {
      return;
    }
    this.cambiandoEstado = true;
    this.empresaService.cambiarEstado(empresa.id_empresa, nuevo).subscribe({
      next: (actualizada) => {
        this.empresa = actualizada;
        this.cambiandoEstado = false;
      },
      error: (err) => {
        this.cambiandoEstado = false;
        alert(mensajeDeError(err, 'No se pudo cambiar el estado de la empresa.'));
      }
    });
  }

  alternarFormulario(empresa: Empresa): void {
    this.mostrarFormulario = !this.mostrarFormulario;
    this.errorSucursal = null;
    if (!this.mostrarFormulario) {
      return;
    }
    // Las sucursales se nombran "<EMPRESA> <Zona>": se deja escrito el nombre de la empresa.
    this.sucursalForm.reset({ nombre: `${empresa.nombre} `, id_ciudad: null });
    if (this.ciudades.length === 0) {
      this.empresaService.ciudades().subscribe({
        next: (data: any) => this.ciudades = data.results || data,
        error: () => this.ciudades = []
      });
    }
  }

  registrarSucursal(empresa: Empresa): void {
    if (this.sucursalForm.invalid) {
      return;
    }
    const valores = this.sucursalForm.value;
    const datos = {
      id_empresa: empresa.id_empresa,
      id_ciudad: valores.id_ciudad,
      nombre: String(valores.nombre || '').trim(),
      direccion: String(valores.direccion || '').trim(),
      telefono: valores.telefono || null,
      fecha_apertura: valores.fecha_apertura || null
    };
    this.guardandoSucursal = true;
    this.errorSucursal = null;
    this.empresaService.crearSucursal(datos).subscribe({
      next: () => {
        this.guardandoSucursal = false;
        this.mostrarFormulario = false;
        // Se recarga la empresa para actualizar sucursales y su total.
        this.cargarEmpresa(empresa.id_empresa);
      },
      error: (err) => {
        this.guardandoSucursal = false;
        this.errorSucursal = mensajeDeError(err, 'No se pudo registrar la sucursal.');
      }
    });
  }
}