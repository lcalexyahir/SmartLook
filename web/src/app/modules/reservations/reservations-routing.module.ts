// web/src/app/modules/reservations/reservations-routing.module.ts
//
// Archivo NUEVO.

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ReservationsPlaceholderComponent } from './pages/reservations-placeholder/reservations-placeholder.component';

const routes: Routes = [
  { path: '', component: ReservationsPlaceholderComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ReservationsRoutingModule { }