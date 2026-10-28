// web/src/app/modules/empresas/pages/empresa-form/empresa-form.component.ts
//
// NUEVO (SaaS): registro y edición de una empresa.
// - /empresas/nueva (SUPER_ADMIN): datos de la empresa, logo, plan y su
//   administrador. La suscripción queda activa desde hoy sin cobro.
// - /empresas/:id/editar: el SUPER_ADMIN edita nombre, NIT, contacto y logo;
//   el ADMIN_EMPRESA solo el logo y el contacto de su empresa.
// MODIFICADO: el logo se sube desde un archivo (PNG, JPG o WebP de hasta
// 10 MB). El navegador lo reduce a 256 px y lo envía en base64; ya no se
// acepta pegar una URL.
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../../../core/auth/auth.service';
import {
  Empresa,
  EmpresaService,
  iniciales,
  mensajeDeError
} from '../../services/empresa.service';

const TIPOS_LOGO = ['image/png', 'image/jpeg', 'image/webp'];
const MAX_BYTES_ARCHIVO = 10 * 1024 * 1024;
const LADO_LOGO = 256;
const TEXTO_PERIODO: { [periodo: string]: string } = {
  MENSUAL: 'mes',
  SEMESTRAL: 'semestre',
  ANUAL: 'año'
};

@Component({
  selector: 'app-empresa-form',
  template: `
    <div class="form-container">
      <a class="volver" [routerLink]="idEmpresa ? ['/empresas', idEmpresa] : ['/empresas']">← Volver</a>
      <h2>{{ idEmpresa ? 'Editar empresa' : 'Registrar empresa' }}</h2>
      <p *ngIf="cargando">Cargando...</p>
      <form *ngIf="!cargando" [formGroup]="form" (ngSubmit)="guardar()">
        <section class="card">
          <h3>Datos de la empresa</h3>
          <div class="logo-row">
            <div class="avatar">
              <img *ngIf="logoActual && !logoRoto" [src]="logoActual" alt="Vista previa del logo"
                   (error)="logoRoto = true">
              <span *ngIf="!logoActual || logoRoto">{{ iniciales(nombreActual) }}</span>
            </div>
            <div class="logo-acciones">
              <label class="etiqueta">Logo</label>
              <input #archivoLogo type="file" accept="image/png,image/jpeg,image/webp" hidden
                     (change)="onArchivoLogo($event)">
              <div class="botones">
                <button type="button" class="btn btn-secundario" [disabled]="procesandoLogo"
                        (click)="archivoLogo.click()">
                  {{ procesandoLogo ? 'Procesando...' : (logoActual ? 'Cambiar logo' : 'Subir logo') }}
                </button>
                <button type="button" class="btn btn-link" *ngIf="logoActual" (click)="quitarLogo()">Quitar logo</button>
              </div>
              <small class="ayuda">PNG, JPG o WebP, hasta 10 MB.</small>
              <small class="campo-error" *ngIf="errorLogo">{{ errorLogo }}</small>
            </div>
          </div>
          <div class="form-row" *ngIf="form.get('nombre')">
            <div class="form-group">
              <label for="nombre">Nombre *</label>
              <input id="nombre" type="text" formControlName="nombre" maxlength="150">
              <small class="campo-error" *ngIf="invalido('nombre')">El nombre es obligatorio.</small>
            </div>
            <div class="form-group">
              <label for="nit">NIT</label>
              <input id="nit" type="text" formControlName="nit" maxlength="30">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="correo_contacto">Correo de contacto</label>
              <input id="correo_contacto" type="email" formControlName="correo_contacto" maxlength="150">
              <small class="campo-error" *ngIf="invalido('correo_contacto')">Correo no válido.</small>
            </div>
            <div class="form-group">
              <label for="telefono">Teléfono</label>
              <input id="telefono" type="text" formControlName="telefono" maxlength="20">
            </div>
          </div>
          <div class="form-group" *ngIf="form.get('id_plan')">
            <label for="plan">Plan *</label>
            <select id="plan" formControlName="id_plan">
              <option [ngValue]="null">-- Selecciona un plan --</option>
              <option *ngFor="let p of planes" [ngValue]="p.id_plan">{{ textoPlan(p) }}</option>
            </select>
            <small class="campo-error" *ngIf="invalido('id_plan')">Selecciona un plan.</small>
            <small class="ayuda">La suscripción queda activa desde hoy por un periodo del plan.</small>
          </div>
        </section>
        <section class="card" *ngIf="form.get('administrador')" formGroupName="administrador">
          <h3>Administrador de la empresa</h3>
          <div class="form-row">
            <div class="form-group">
              <label for="adm_nombres">Nombres *</label>
              <input id="adm_nombres" type="text" formControlName="nombres" maxlength="100">
            </div>
            <div class="form-group">
              <label for="adm_apellidos">Apellidos *</label>
              <input id="adm_apellidos" type="text" formControlName="apellidos" maxlength="100">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="adm_correo">Correo (usuario de inicio de sesión) *</label>
              <input id="adm_correo" type="email" formControlName="correo" maxlength="150">
              <small class="campo-error" *ngIf="invalido('administrador.correo')">Correo no válido.</small>
            </div>
            <div class="form-group">
              <label for="adm_telefono">Teléfono</label>
              <input id="adm_telefono" type="text" formControlName="telefono" maxlength="20">
            </div>
          </div>
          <div class="form-group">
            <label for="adm_password">Contraseña *</label>
            <input id="adm_password" type="password" formControlName="password" autocomplete="new-password">
            <small class="campo-error" *ngIf="invalido('administrador.password')">Mínimo 8 caracteres.</small>
            <small class="ayuda">Al menos 8 caracteres, con una letra y un número.</small>
          </div>
        </section>
        <p class="error" *ngIf="error">{{ error }}</p>
        <div class="acciones">
          <button type="submit" class="btn btn-primary" [disabled]="form.invalid || guardando">
            {{ guardando ? 'Guardando...' : (idEmpresa ? 'Guardar cambios' : 'Registrar empresa') }}
          </button>
        </div>
      </form>
    </div>
  `,
  styles: [`
    .form-container { padding: 2rem; max-width: 820px; margin: 0 auto; }
    .volver { color: #0f3460; text-decoration: none; font-size: 0.9rem; }
    h2 { color: #1a1a2e; margin: 0.5rem 0 1.25rem; }
    .card {
      background: white; border-radius: 10px; padding: 1.5rem;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); margin-bottom: 1.25rem;
    }
    .card h3 { color: #1a1a2e; font-size: 1.05rem; margin-bottom: 1rem; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .form-group { margin-bottom: 1rem; }
    .form-group label { display: block; margin-bottom: 0.35rem; font-weight: 600; font-size: 0.9rem; }
    .form-group input, .form-group select {
      width: 100%; padding: 0.6rem; border-radius: 6px; border: 1px solid #ccc; font-size: 0.95rem;
    }
    .campo-error { display: block; color: #c0392b; font-size: 0.8rem; margin-top: 0.25rem; }
    .ayuda { display: block; color: #888; font-size: 0.8rem; margin-top: 0.25rem; }
    .logo-row { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
    .logo-acciones { flex: 1; }
    .etiqueta { display: block; margin-bottom: 0.35rem; font-weight: 600; font-size: 0.9rem; }
    .botones { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .btn-secundario { background: white; color: #1a1a2e; border: 1px solid #1a1a2e; }
    .btn-secundario:hover { background: #f0f2f7; }
    .btn-link {
      background: none; border: none; color: #c0392b; cursor: pointer;
      text-decoration: underline; padding: 0; font-weight: 500;
    }
    .avatar {
      width: 80px; height: 80px; flex-shrink: 0; border-radius: 50%; overflow: hidden;
      background: #1a1a2e; color: white; display: flex; align-items: center; justify-content: center;
      font-weight: 700; font-size: 1.4rem; border: 2px solid #e0e0e0;
    }
    .avatar img { width: 100%; height: 100%; object-fit: cover; background: white; }
    .error { color: #c0392b; margin-bottom: 1rem; }
    .acciones { display: flex; justify-content: flex-end; }
    @media (max-width: 768px) {
      .form-container { padding: 1rem; }
      .form-row { grid-template-columns: 1fr; gap: 0; }
      .logo-row { flex-direction: column; align-items: center; text-align: center; }
      .botones { justify-content: center; }
      .acciones .btn { width: 100%; }
    }
  `]
})
export class EmpresaFormComponent implements OnInit {
  form!: FormGroup;
  idEmpresa: number | null = null;
  esSuperAdmin = false;
  planes: any[] = [];
  cargando = false;
  guardando = false;
  error: string | null = null;
  logoRoto = false;
  procesandoLogo = false;
  errorLogo: string | null = null;
  private empresa: Empresa | null = null;
  iniciales = iniciales;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private empresaService: EmpresaService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.esSuperAdmin = this.authService.obtenerRoles().includes('SUPER_ADMIN');
    const id = this.route.snapshot.paramMap.get('id');
    this.idEmpresa = id ? Number(id) : null;
    this.form = this.fb.group({
      nombre: ['', [Validators.required, Validators.maxLength(150)]],
      nit: [''],
      correo_contacto: ['', Validators.email],
      telefono: [''],
      logo: [''],
      id_plan: [null, Validators.required],
      administrador: this.fb.group({
        nombres: ['', Validators.required],
        apellidos: ['', Validators.required],
        correo: ['', [Validators.required, Validators.email]],
        telefono: [''],
        password: ['', [Validators.required, Validators.minLength(8)]]
      })
    });
    if (this.idEmpresa) {
      this.prepararEdicion(this.idEmpresa);
    } else {
      this.empresaService.planes().subscribe({
        next: (data: any) => {
          this.planes = (data.results || data).filter((p: any) => p.estado);
        },
        error: () => this.planes = []
      });
    }
  }

  // En edición no se cambian plan ni administrador; el ADMIN_EMPRESA tampoco nombre ni NIT.
  private prepararEdicion(id: number): void {
    this.form.removeControl('id_plan');
    this.form.removeControl('administrador');
    if (!this.esSuperAdmin) {
      this.form.removeControl('nombre');
      this.form.removeControl('nit');
    }
    this.cargando = true;
    this.empresaService.obtener(id).subscribe({
      next: (empresa) => {
        this.empresa = empresa;
        this.form.patchValue({
          nombre: empresa.nombre,
          nit: empresa.nit || '',
          correo_contacto: empresa.correo_contacto || '',
          telefono: empresa.telefono || '',
          logo: empresa.logo || ''
        });
        this.cargando = false;
      },
      error: (err) => {
        this.cargando = false;
        this.error = mensajeDeError(err, 'No se encontró la empresa.');
      }
    });
  }

  get logoActual(): string {
    return this.form?.get('logo')?.value || '';
  }

  get nombreActual(): string {
    return this.form?.get('nombre')?.value || this.empresa?.nombre || '';
  }

  // Valida el archivo elegido, lo reduce a 256 px y lo deja en el formulario como base64.
  onArchivoLogo(evento: Event): void {
    const entrada = evento.target as HTMLInputElement;
    const archivo = entrada.files?.[0];
    entrada.value = '';
    if (!archivo) {
      return;
    }
    this.errorLogo = null;
    if (!TIPOS_LOGO.includes(archivo.type)) {
      this.errorLogo = 'El logo debe ser una imagen PNG, JPG o WebP.';
      return;
    }
    if (archivo.size > MAX_BYTES_ARCHIVO) {
      this.errorLogo = 'El archivo supera los 10 MB.';
      return;
    }
    this.procesandoLogo = true;
    this.reducirImagen(archivo)
      .then((base64) => {
        const control = this.form.get('logo');
        control?.setValue(base64);
        control?.markAsDirty();
        this.logoRoto = false;
      })
      .catch(() => this.errorLogo = 'No se pudo leer la imagen. Prueba con otro archivo.')
      .finally(() => this.procesandoLogo = false);
  }

  quitarLogo(): void {
    const control = this.form.get('logo');
    control?.setValue('');
    control?.markAsDirty();
    this.errorLogo = null;
  }

  // Dibuja la imagen en un canvas de máximo 256 px por lado (sin recortar ni
  // agrandar) y la devuelve como WebP en base64; si el navegador no genera
  // WebP, toDataURL devuelve PNG, que el backend también acepta.
  private reducirImagen(archivo: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(archivo);
      const imagen = new Image();
      imagen.onload = () => {
        const escala = Math.min(1, LADO_LOGO / Math.max(imagen.width, imagen.height));
        const ancho = Math.max(1, Math.round(imagen.width * escala));
        const alto = Math.max(1, Math.round(imagen.height * escala));
        const canvas = document.createElement('canvas');
        canvas.width = ancho;
        canvas.height = alto;
        const contexto = canvas.getContext('2d');
        URL.revokeObjectURL(url);
        if (!contexto) {
          reject(new Error('Sin canvas'));
          return;
        }
        contexto.drawImage(imagen, 0, 0, ancho, alto);
        resolve(canvas.toDataURL('image/webp', 0.9));
      };
      imagen.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error('Imagen inválida'));
      };
      imagen.src = url;
    });
  }

  invalido(campo: string): boolean {
    const control = this.form.get(campo);
    return !!control && control.invalid && (control.dirty || control.touched);
  }

  textoPlan(plan: any): string {
    const periodo = TEXTO_PERIODO[plan.periodo] || plan.periodo;
    return `${plan.nombre} · USD ${Number(plan.precio_usd)} por ${periodo} (Bs ${Number(plan.precio_bob)})`;
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.guardando = true;
    this.error = null;
    const datos = this.form.value;
    const peticion = this.idEmpresa
      ? this.empresaService.actualizar(this.idEmpresa, datos)
      : this.empresaService.crear(datos);
    peticion.subscribe({
      next: (empresa) => {
        this.guardando = false;
        this.router.navigate(['/empresas', empresa.id_empresa]);
      },
      error: (err) => {
        this.guardando = false;
        this.error = mensajeDeError(err, 'No se pudo guardar la empresa.');
      }
    });
  }
}