// web/src/app/modules/clients/clients-routing.module.ts
//
// Archivo NUEVO.

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ClientListComponent } from './pages/client-list/client-list.component';

const routes: Routes = [
  { path: '', component: ClientListComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ClientsRoutingModule { }