import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PosCartComponent } from './pages/pos-cart/pos-cart.component';

const routes: Routes = [
  { path: '', component: PosCartComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PosRoutingModule { }