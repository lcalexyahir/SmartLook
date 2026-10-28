// web/src/app/modules/dashboard/pages/dashboard-home/dashboard-home.component.ts
//
// Archivo YA EXISTENTE (antes era una clase vacía). Ahora carga los
// KPIs reales desde GET /api/bi/dashboard/.
// NUEVO (SaaS - A.4): debajo de los KPIs muestra el comparativo entre
// sucursales a quien puede verlo (SUPER_ADMIN, ADMIN_EMPRESA y encargado).
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../../../core/services/api.service';
import { AuthService } from '../../../../core/auth/auth.service';
const ROLES_COMPARATIVO = ['SUPER_ADMIN', 'ADMIN_EMPRESA', 'ENCARGADO_SUCURSAL'];
interface DashboardKpis {
  total_clientes: number;
  total_productos: number;
  total_sucursales: number;
  total_proveedores: number;
  stock_total: number;
  productos_stock_bajo: number;
  total_ventas_pos: number;
  monto_total_ventas: string;
  total_ordenes: number;
  reservas_pendientes: number;
}
@Component({
  selector: 'app-dashboard-home',
  templateUrl: './dashboard-home.component.html',
  styleUrls: ['./dashboard-home.component.css']
})
export class DashboardHomeComponent implements OnInit {
  kpis: DashboardKpis | null = null;
  cargando = true;
  puedeVerComparativo = false;
  esSuperAdmin = false;
  constructor(private apiService: ApiService, private authService: AuthService) {}
  ngOnInit(): void {
    const roles = this.authService.obtenerRoles();
    this.puedeVerComparativo = roles.some(rol => ROLES_COMPARATIVO.includes(rol));
    this.esSuperAdmin = roles.includes('SUPER_ADMIN');
    this.apiService.get<DashboardKpis>('/bi/dashboard/').subscribe({
      next: (data) => {
        this.kpis = data;
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
      }
    });
  }
}