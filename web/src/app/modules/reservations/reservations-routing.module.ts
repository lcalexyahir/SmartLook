// web/src/app/modules/reservations/reservations-routing.module.ts
//
// MODIFICADO (CU11/CU12/CU13): la raíz ahora muestra la lista de
// reservas (ReservationListComponent) - "Mis Reservas" para el cliente,
// "Reservas" para el encargado. "nueva" lleva al formulario de creación.

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ReservationListComponent } from './pages/reservation-list/reservation-list.component';
import { ReservationFormComponent } from './pages/reservation-form/reservation-form.component';

const routes: Routes = [
  { path: '', component: ReservationListComponent },
  { path: 'nueva', component: ReservationFormComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ReservationsRoutingModule { }