// web/src/app/modules/products/products-routing.module.ts
//
// Archivo NUEVO.

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ProductManagementComponent } from './pages/product-management/product-management.component';

const routes: Routes = [
  { path: '', component: ProductManagementComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ProductsRoutingModule { }