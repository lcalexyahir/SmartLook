// web/src/app/modules/assistant-admin/assistant-admin.module.ts
//
// NUEVO (CU20): módulo del asistente de gestión, cargado solo por la ruta
// protegida /assistant-admin (ver app-routing.module.ts).
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AssistantAdminRoutingModule } from './assistant-admin-routing.module';
import { AssistantAdminHomeComponent } from './pages/assistant-admin-home/assistant-admin-home.component';

@NgModule({
  declarations: [AssistantAdminHomeComponent],
  imports: [CommonModule, FormsModule, AssistantAdminRoutingModule]
})
export class AssistantAdminModule {}