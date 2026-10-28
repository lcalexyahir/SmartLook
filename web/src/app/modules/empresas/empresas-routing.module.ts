// web/src/app/modules/empresas/empresas-routing.module.ts
//
// NUEVO (SaaS): rutas de empresas. Registrar una empresa es solo del
// SUPER_ADMIN; el ADMIN_EMPRESA entra al detalle y edición de la suya.
// NUEVO (SaaS - A.3): 'plan' (Mi plan) solo para el ADMIN_EMPRESA; va antes
// de ':id' para que no se confunda con el id de una empresa.
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { RoleGuard } from '../../core/auth/role.guard';
import { EmpresaListComponent } from './pages/empresa-list/empresa-list.component';
import { EmpresaFormComponent } from './pages/empresa-form/empresa-form.component';
import { EmpresaDetailComponent } from './pages/empresa-detail/empresa-detail.component';
import { MiPlanComponent } from './pages/mi-plan/mi-plan.component';
const routes: Routes = [
  { path: '', component: EmpresaListComponent },
  {
    path: 'nueva',
    component: EmpresaFormComponent,
    canActivate: [RoleGuard],
    data: { rolesExcluidos: ['ADMIN_EMPRESA', 'ENCARGADO_SUCURSAL', 'CAJERO', 'REPARTIDOR', 'CLIENTE'] }
  },
  {
    path: 'plan',
    component: MiPlanComponent,
    canActivate: [RoleGuard],
    data: { rolesExcluidos: ['SUPER_ADMIN', 'ENCARGADO_SUCURSAL', 'CAJERO', 'REPARTIDOR', 'CLIENTE'] }
  },
  { path: ':id', component: EmpresaDetailComponent },
  { path: ':id/editar', component: EmpresaFormComponent }
];
@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class EmpresasRoutingModule { }