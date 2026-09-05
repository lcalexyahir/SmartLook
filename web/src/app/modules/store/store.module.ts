import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';

import { StoreRoutingModule } from './store-routing.module';
import { BranchManagementComponent } from './pages/branch-management/branch-management.component';
import { SupplierManagementComponent } from './pages/supplier-management/supplier-management.component';

@NgModule({
  declarations: [
    BranchManagementComponent,
    SupplierManagementComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    StoreRoutingModule
  ]
})
export class StoreModule { }