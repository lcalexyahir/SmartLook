import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { StockListComponent } from './pages/stock-list/stock-list.component';
import { MovementHistoryComponent } from './pages/movement-history/movement-history.component';

const routes: Routes = [
  { path: 'stock', component: StockListComponent },
  { path: 'movimientos', component: MovementHistoryComponent },
  { path: '', redirectTo: 'stock', pathMatch: 'full' }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class InventoryRoutingModule { }