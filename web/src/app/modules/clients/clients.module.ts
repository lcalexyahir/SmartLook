// web/src/app/modules/clients/clients.module.ts
//
// Archivo NUEVO. Incluye FormsModule por el buscador con [(ngModel)].

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ClientsRoutingModule } from './clients-routing.module';
import { ClientListComponent } from './pages/client-list/client-list.component';

@NgModule({
  declarations: [
    ClientListComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ClientsRoutingModule
  ]
})
export class ClientsModule { }