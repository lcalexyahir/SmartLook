import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';

import { CatalogRoutingModule } from './catalog-routing.module';
import { ProductListComponent } from './pages/product-list/product-list.component';
import { ProductDetailComponent } from './pages/product-detail/product-detail.component';
import { SharedModule } from '../../shared/shared.module';
import { AssistantModule } from '../assistant/assistant.module';

@NgModule({
  declarations: [
    ProductListComponent,
    ProductDetailComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    SharedModule,
    AssistantModule,
    CatalogRoutingModule
  ]
})
export class CatalogModule { }