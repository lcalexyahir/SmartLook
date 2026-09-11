// web/src/app/modules/permissions/permissions-routing.module.ts
//
// Archivo NUEVO.

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PermissionManagementComponent } from './pages/permission-management/permission-management.component';

const routes: Routes = [
  { path: '', component: PermissionManagementComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PermissionsRoutingModule { }