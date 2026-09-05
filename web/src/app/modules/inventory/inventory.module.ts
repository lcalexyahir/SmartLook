import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';


import { InventoryRoutingModule } from './inventory-routing.module';

import { StockListComponent } from './pages/stock-list/stock-list.component';
import { MovementHistoryComponent } from './pages/movement-history/movement-history.component';


import { SharedModule } from '../../shared/shared.module';



@NgModule({

  declarations: [

    StockListComponent,

    MovementHistoryComponent

  ],


  imports: [

    CommonModule,

    ReactiveFormsModule,

    InventoryRoutingModule,

    SharedModule

  ]

})
export class InventoryModule { }