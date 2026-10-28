// web/src/app/modules/profile/profile-routing.module.ts
//
// MODIFICADO: el placeholder se reemplaza por la página de perfil real.
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ProfilePageComponent } from './pages/profile-page/profile-page.component';
const routes: Routes = [
  { path: '', component: ProfilePageComponent }
];
@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ProfileRoutingModule { }