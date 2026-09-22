// web/src/app/modules/assistant-admin/assistant-admin-routing.module.ts
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AssistantAdminHomeComponent } from './pages/assistant-admin-home/assistant-admin-home.component';

const routes: Routes = [
  {
    path: '',
    component: AssistantAdminHomeComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AssistantAdminRoutingModule {}