// web/src/app/modules/users/users-routing.module.ts
//
// Archivo NUEVO.

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { UserManagementComponent } from './pages/user-management/user-management.component';

const routes: Routes = [
  { path: '', component: UserManagementComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class UsersRoutingModule { }