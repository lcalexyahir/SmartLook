import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { DashboardHomeComponent }
from './pages/dashboard-home/dashboard-home.component';

import { InventoryDashboardComponent }
from './pages/inventory-dashboard/inventory-dashboard.component';

import { SalesDashboardComponent }
from './pages/sales-dashboard/sales-dashboard.component';


const routes: Routes = [

  {
    path: '',
    component: DashboardHomeComponent
  },

  {
    path: 'inventory',
    component: InventoryDashboardComponent
  },

  {
    path: 'sales',
    component: SalesDashboardComponent
  }

];


@NgModule({

  imports: [
    RouterModule.forChild(routes)
  ],

  exports: [
    RouterModule
  ]

})
export class DashboardRoutingModule {}