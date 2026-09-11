// web/src/app/modules/profile/profile-routing.module.ts
//
// Archivo NUEVO.

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ProfilePlaceholderComponent } from './pages/profile-placeholder/profile-placeholder.component';

const routes: Routes = [
  { path: '', component: ProfilePlaceholderComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ProfileRoutingModule { }