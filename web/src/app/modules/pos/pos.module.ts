import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { PosRoutingModule } from './pos-routing.module';
import { PosCartComponent } from './pages/pos-cart/pos-cart.component';

@NgModule({
  declarations: [
    PosCartComponent
  ],
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    PosRoutingModule
  ]
})
export class PosModule { }