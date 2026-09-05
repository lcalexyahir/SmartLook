import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';


const routes: Routes = [

  {
    path: 'auth',
    loadChildren: () =>
      import('./modules/auth/auth.module')
        .then(m => m.AuthModule)
  },


  {
    path: 'catalog',
    loadChildren: () =>
      import('./modules/catalog/catalog.module')
        .then(m => m.CatalogModule)
  },


  {
    path: 'inventory',
    loadChildren: () =>
      import('./modules/inventory/inventory.module')
        .then(m => m.InventoryModule)
  },


  {
    path: 'store',
    loadChildren: () =>
      import('./modules/store/store.module')
        .then(m => m.StoreModule)
  },


  // Ruta inicial: enviar al login
  {
    path: '',
    redirectTo: 'auth/login',
    pathMatch: 'full'
  },


  // Cualquier ruta inexistente también vuelve al login
  {
    path: '**',
    redirectTo: 'auth/login'
  }

];


@NgModule({

  imports: [
    RouterModule.forRoot(routes)
  ],

  exports: [
    RouterModule
  ]

})
export class AppRoutingModule {}