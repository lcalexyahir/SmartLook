// web/src/app/modules/users/users.module.ts
//
// Archivo NUEVO. Este es el módulo que app-routing.module.ts ya venía
// referenciando (loadChildren) pero que nunca se había creado.

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';

import { UsersRoutingModule } from './users-routing.module';
import { UserManagementComponent } from './pages/user-management/user-management.component';

@NgModule({
  declarations: [
    UserManagementComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    UsersRoutingModule
  ]
})
export class UsersModule { }