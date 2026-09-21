import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { OrdersPageComponent } from './pages/orders-page/orders-page.component';

@NgModule({
  declarations: [
    OrdersPageComponent
  ],
  imports: [
    CommonModule,
    RouterModule.forChild([
      { path: '', component: OrdersPageComponent }
    ])
  ]
})
export class OrdersModule { }