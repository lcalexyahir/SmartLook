import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { DeliveriesPageComponent } from './pages/deliveries-page/deliveries-page.component';

@NgModule({
  declarations: [
    DeliveriesPageComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule.forChild([
      { path: '', component: DeliveriesPageComponent }
    ])
  ]
})
export class DeliveriesModule { }