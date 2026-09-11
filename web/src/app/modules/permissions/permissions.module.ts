// web/src/app/modules/permissions/permissions.module.ts
//
// Archivo NUEVO.

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { PermissionsRoutingModule } from './permissions-routing.module';
import { PermissionManagementComponent } from './pages/permission-management/permission-management.component';

@NgModule({
  declarations: [
    PermissionManagementComponent
  ],
  imports: [
    CommonModule,
    PermissionsRoutingModule
  ]
})
export class PermissionsModule { }