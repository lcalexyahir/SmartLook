// web/src/app/modules/empresas/pages/empresa-list/empresa-list.component.ts
//
// NUEVO (SaaS): lista de empresas con su logo como foto de perfil, plan,
// vencimiento de la suscripción y cantidad de sucursales (SUPER_ADMIN).
// El ADMIN_EMPRESA no tiene lista: se le lleva directo al detalle de su empresa.
import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../../core/auth/auth.service';
import {
  Empresa,
  EmpresaService,
  formatoFecha,
  iniciales,
  mensajeDeError
} from '../../services/empresa.service';

@Component({
  selector: 'app-empresa-list',
  template: `
    <div class="empresas-container">
      <div class="header">
        <h2>Empresas</h2>
        <a *ngIf="esSuperAdmin" routerLink="/empresas/nueva" class="btn btn-primary">Registrar empresa</a>
      </div>
      <p *ngIf="cargando">Cargando empresas...</p>
      <p class="error" *ngIf="error">{{ error }}</p>
      <div class="grid" *ngIf="!cargando">
        <a class="empresa-card" *ngFor="let e of empresas" [routerLink]="['/empresas', e.id_empresa]">
          <div class="avatar">
            <img *ngIf="e.logo && !logoRoto[e.id_empresa]" [src]="e.logo" [alt]="'Logo de ' + e.nombre"
                 (error)="logoRoto[e.id_empresa] = true">
            <span *ngIf="!e.logo || logoRoto[e.id_empresa]">{{ iniciales(e.nombre) }}</span>
          </div>
          <div class="info">
            <div class="titulo">
              <h3>{{ e.nombre }}</h3>
              <span class="badge" [class.activa]="e.estado === 'ACTIVA'">{{ e.estado }}</span>
            </div>
            <p>Plan {{ e.suscripcion?.plan_nombre || '-' }} · {{ e.total_sucursales }} sucursal(es)</p>
            <p *ngIf="e.suscripcion as s" class="vence" [class.alerta]="s.dias_restantes <= 7">
              {{ s.dias_restantes < 0 ? 'Venció' : 'Vence' }} el {{ formatoFecha(s.fecha_vencimiento) }}
              <span *ngIf="s.dias_restantes >= 0">({{ s.dias_restantes }} días)</span>
            </p>
            <p *ngIf="!e.suscripcion" class="vence alerta">Sin suscripción</p>
          </div>
        </a>
      </div>
      <p class="empty" *ngIf="!cargando && !error && empresas.length === 0">No hay empresas registradas.</p>
    </div>
  `,
  styles: [`
    .empresas-container { padding: 2rem; max-width: 1200px; margin: 0 auto; }
    .header {
      display: flex; justify-content: space-between; align-items: center;
      gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem;
    }
    .header h2 { color: #1a1a2e; }
    .header .btn { text-decoration: none; display: inline-block; }
    .error { color: #c0392b; margin-bottom: 1rem; }
    .empty { color: #999; text-align: center; padding: 2rem; }
    .grid {
      display: grid; gap: 1rem;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    }
    .empresa-card {
      display: flex; gap: 1rem; align-items: center;
      background: white; border-radius: 10px; padding: 1rem 1.25rem;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      text-decoration: none; color: inherit;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .empresa-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12); }
    .avatar {
      width: 64px; height: 64px; flex-shrink: 0; border-radius: 50%;
      overflow: hidden; background: #1a1a2e; color: white;
      display: flex; align-items: center; justify-content: center;
      font-weight: 700; font-size: 1.2rem; border: 2px solid #e0e0e0;
    }
    .avatar img { width: 100%; height: 100%; object-fit: cover; background: white; }
    .info { min-width: 0; flex: 1; }
    .titulo { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
    .titulo h3 { font-size: 1.05rem; color: #1a1a2e; margin: 0; }
    .info p { font-size: 0.85rem; color: #666; margin-top: 0.25rem; }
    .vence.alerta { color: #c0392b; font-weight: 600; }
    .badge {
      padding: 0.15rem 0.6rem; border-radius: 20px; font-size: 0.7rem;
      font-weight: 600; background: #fdecea; color: #c0392b;
    }
    .badge.activa { background: #e8f5e9; color: #2e7d32; }
    @media (max-width: 768px) {
      .empresas-container { padding: 1rem; }
      .grid { grid-template-columns: 1fr; }
    }
  `]
})
export class EmpresaListComponent implements OnInit {
  empresas: Empresa[] = [];
  cargando = true;
  error: string | null = null;
  esSuperAdmin = false;
  logoRoto: { [id: number]: boolean } = {};
  iniciales = iniciales;
  formatoFecha = formatoFecha;

  constructor(
    private empresaService: EmpresaService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.esSuperAdmin = this.authService.obtenerRoles().includes('SUPER_ADMIN');
    this.empresaService.listar().subscribe({
      next: (data: any) => {
        this.empresas = data.results || data;
        this.cargando = false;
        // El ADMIN_EMPRESA solo tiene su empresa: va directo a su detalle.
        if (!this.esSuperAdmin && this.empresas.length > 0) {
          this.router.navigate(['/empresas', this.empresas[0].id_empresa], { replaceUrl: true });
        }
      },
      error: (err) => {
        this.cargando = false;
        this.error = mensajeDeError(err, 'No se pudieron cargar las empresas.');
      }
    });
  }
}