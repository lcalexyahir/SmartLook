import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { BranchManagementComponent } from './pages/branch-management/branch-management.component';
import { SupplierManagementComponent } from './pages/supplier-management/supplier-management.component';

const routes: Routes = [
  { path: 'sucursales', component: BranchManagementComponent },
  { path: 'proveedores', component: SupplierManagementComponent },
  { path: '', redirectTo: 'sucursales', pathMatch: 'full' }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class StoreRoutingModule { }