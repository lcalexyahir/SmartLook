// web/src/app/modules/reservations/reservations.module.ts
//
// MODIFICADO (CU11/CU12/CU13): declara ReservationListComponent además
// del formulario. El placeholder ya no se usa en ninguna ruta, pero se
// deja declarado por si hace falta.

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ReservationsRoutingModule } from './reservations-routing.module';
import { ReservationsPlaceholderComponent } from './pages/reservations-placeholder/reservations-placeholder.component';
import { ReservationFormComponent } from './pages/reservation-form/reservation-form.component';
import { ReservationListComponent } from './pages/reservation-list/reservation-list.component';

@NgModule({
  declarations: [
    ReservationsPlaceholderComponent,
    ReservationFormComponent,
    ReservationListComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    ReservationsRoutingModule
  ]
})
export class ReservationsModule { }