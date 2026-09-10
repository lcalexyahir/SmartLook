import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { UserManagementComponent } from './pages/user-management/user-management.component';
import { UserFormComponent } from './pages/user-form/user-form.component';

const routes: Routes = [

  {
    path: '',
    component: UserManagementComponent
  },

  {
    path: 'nuevo',
    component: UserFormComponent
  }

];


@NgModule({

  imports: [
    RouterModule.forChild(routes)
  ],

  exports: [
    RouterModule
  ]

})
export class UsersRoutingModule {}