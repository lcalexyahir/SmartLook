import { NgModule } from '@angular/core';

import {
  RouterModule,
  Routes
} from '@angular/router';


import { LayoutComponent } from './layout/layout.component';



const routes: Routes = [


  {
    path: 'auth',
    loadChildren: () =>
      import('./modules/auth/auth.module')
        .then(m => m.AuthModule)
  },


  {
    path: '',
    component: LayoutComponent,

    children: [

      {
        path: 'dashboard',
        loadChildren: () =>
          import('./modules/dashboard/dashboard.module')
            .then(m => m.DashboardModule)
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

      {
        path: 'users',
        loadChildren: () =>
          import('./modules/users/users.module')
            .then(m => m.UsersModule)
      }

    ]

  },


  {
    path: '',
    redirectTo: 'auth/login',
    pathMatch: 'full'
  },


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