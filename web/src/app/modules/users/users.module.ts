import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { UsersRoutingModule } from './users-routing.module';

import { UserManagementComponent } 
from './pages/user-management/user-management.component';

import { UserFormComponent } 
from './pages/user-form/user-form.component';
import { ReactiveFormsModule } from '@angular/forms';

@NgModule({

  declarations: [

    UserManagementComponent,
    UserFormComponent

  ],

  imports: [

    CommonModule,

    UsersRoutingModule,
    ReactiveFormsModule

  ]

})
export class UsersModule {}