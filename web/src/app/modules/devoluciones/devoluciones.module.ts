// web/src/app/modules/devoluciones/devoluciones.module.ts
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { DevolucionesListComponent } from './pages/devoluciones-list/devoluciones-list.component';

@NgModule({
  declarations: [
    DevolucionesListComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule.forChild([
      { path: '', component: DevolucionesListComponent }
    ])
  ]
})
export class DevolucionesModule { }