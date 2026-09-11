// web/src/app/modules/bitacora/bitacora.module.ts
//
// Archivo NUEVO. Incluye FormsModule por el filtro con [(ngModel)].

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { BitacoraRoutingModule } from './bitacora-routing.module';
import { BitacoraListComponent } from './pages/bitacora-list/bitacora-list.component';

@NgModule({
  declarations: [
    BitacoraListComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    BitacoraRoutingModule
  ]
})
export class BitacoraModule { }