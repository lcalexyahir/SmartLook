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



@NgModule({

  declarations: [

    DashboardHomeComponent,

    InventoryDashboardComponent,

    SalesDashboardComponent

  ],

  imports: [

    CommonModule,

    SharedModule,

    DashboardRoutingModule

  ]

})
export class DashboardModule {}