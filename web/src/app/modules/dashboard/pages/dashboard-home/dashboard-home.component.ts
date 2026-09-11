// web/src/app/modules/dashboard/pages/dashboard-home/dashboard-home.component.ts
//
// Archivo YA EXISTENTE (antes era una clase vacía). Ahora carga los
// KPIs reales desde GET /api/bi/dashboard/.

import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../../../core/services/api.service';

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

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
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