// web/src/app/modules/attributes/attributes.module.ts
//
// Archivo NUEVO.

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';

import { AttributesRoutingModule } from './attributes-routing.module';
import { AttributeManagementComponent } from './pages/attribute-management/attribute-management.component';

@NgModule({
  declarations: [
    AttributeManagementComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    AttributesRoutingModule
  ]
})
export class AttributesModule { }