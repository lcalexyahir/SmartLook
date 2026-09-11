// web/src/app/modules/attributes/attributes-routing.module.ts
//
// Archivo NUEVO.

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AttributeManagementComponent } from './pages/attribute-management/attribute-management.component';

const routes: Routes = [
  { path: '', component: AttributeManagementComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AttributesRoutingModule { }