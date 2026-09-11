// web/src/app/modules/products/products.module.ts
//
// Archivo NUEVO.

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';

import { ProductsRoutingModule } from './products-routing.module';
import { ProductManagementComponent } from './pages/product-management/product-management.component';

@NgModule({
  declarations: [
    ProductManagementComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ProductsRoutingModule
  ]
})
export class ProductsModule { }