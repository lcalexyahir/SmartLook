// web/src/app/modules/profile/profile.module.ts
//
// Archivo NUEVO.

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ProfileRoutingModule } from './profile-routing.module';
import { ProfilePlaceholderComponent } from './pages/profile-placeholder/profile-placeholder.component';

@NgModule({
  declarations: [
    ProfilePlaceholderComponent
  ],
  imports: [
    CommonModule,
    ProfileRoutingModule
  ]
})
export class ProfileModule { }