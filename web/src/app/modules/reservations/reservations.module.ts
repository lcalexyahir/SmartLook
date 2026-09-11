// web/src/app/modules/reservations/reservations.module.ts
//
// Archivo NUEVO.

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ReservationsRoutingModule } from './reservations-routing.module';
import { ReservationsPlaceholderComponent } from './pages/reservations-placeholder/reservations-placeholder.component';

@NgModule({
  declarations: [
    ReservationsPlaceholderComponent
  ],
  imports: [
    CommonModule,
    ReservationsRoutingModule
  ]
})
export class ReservationsModule { }