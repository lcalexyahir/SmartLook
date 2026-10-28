// web/src/app/modules/empresas/empresas.module.ts
//
// NUEVO (SaaS): módulo de empresas (lista, registro, edición y detalle con sucursales).
// NUEVO (SaaS - A.3): Mi plan del ADMIN_EMPRESA.
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { EmpresasRoutingModule } from './empresas-routing.module';
import { EmpresaListComponent } from './pages/empresa-list/empresa-list.component';
import { EmpresaFormComponent } from './pages/empresa-form/empresa-form.component';
import { EmpresaDetailComponent } from './pages/empresa-detail/empresa-detail.component';
import { MiPlanComponent } from './pages/mi-plan/mi-plan.component';
@NgModule({
  declarations: [
    EmpresaListComponent,
    EmpresaFormComponent,
    EmpresaDetailComponent,
    MiPlanComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    EmpresasRoutingModule
  ]
})
export class EmpresasModule { }