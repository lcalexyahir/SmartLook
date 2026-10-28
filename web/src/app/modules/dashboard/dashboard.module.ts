// web/src/app/modules/dashboard/dashboard.module.ts
//
// NUEVO (SaaS - A.4): declara el comparativo entre sucursales.
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { SharedModule } from '../../shared/shared.module';
import { DashboardHomeComponent }
from './pages/dashboard-home/dashboard-home.component';
import { InventoryDashboardComponent }
from './pages/inventory-dashboard/inventory-dashboard.component';
import { SalesDashboardComponent }
from './pages/sales-dashboard/sales-dashboard.component';
import { ComparativoSucursalesComponent }
from './components/comparativo-sucursales/comparativo-sucursales.component';
@NgModule({
  declarations: [
    DashboardHomeComponent,
    InventoryDashboardComponent,
    SalesDashboardComponent,
    ComparativoSucursalesComponent
  ],
  imports: [
    CommonModule,
    SharedModule,
    DashboardRoutingModule
  ]
})
export class DashboardModule {}