import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CartRoutingModule } from './cart-routing.module';
import { CartPageComponent } from './pages/cart-page/cart-page.component';

@NgModule({
  declarations: [
    CartPageComponent
  ],
  imports: [
    CommonModule,
    RouterModule,
    CartRoutingModule
  ]
})
export class CartModule { }