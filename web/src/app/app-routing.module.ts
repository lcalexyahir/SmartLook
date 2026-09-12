// web/src/app/app-routing.module.ts
//
// MODIFICADO (CU14): se agrega la ruta 'cart'.

import { NgModule } from '@angular/core';
import {
  RouterModule,
  Routes
} from '@angular/router';
import { LayoutComponent } from './layout/layout.component';
import { AuthGuard } from './core/auth/auth.guard';
import { RoleGuard } from './core/auth/role.guard';

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
        canActivate: [AuthGuard, RoleGuard],
        data: { rolesExcluidos: ['CLIENTE'] },
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
        path: 'cart',
        canActivate: [AuthGuard],
        loadChildren: () =>
          import('./modules/cart/cart.module')
            .then(m => m.CartModule)
      },
      {
        path: 'inventory',
        canActivate: [AuthGuard, RoleGuard],
        data: { rolesExcluidos: ['CLIENTE'] },
        loadChildren: () =>
          import('./modules/inventory/inventory.module')
            .then(m => m.InventoryModule)
      },
      {
        path: 'store',
        canActivate: [AuthGuard, RoleGuard],
        data: { rolesExcluidos: ['CLIENTE'] },
        loadChildren: () =>
          import('./modules/store/store.module')
            .then(m => m.StoreModule)
      },
      {
        path: 'users',
        canActivate: [AuthGuard, RoleGuard],
        data: { rolesExcluidos: ['CLIENTE'] },
        loadChildren: () =>
          import('./modules/users/users.module')
            .then(m => m.UsersModule)
      },
      {
        path: 'permissions',
        canActivate: [AuthGuard, RoleGuard],
        data: { rolesExcluidos: ['CLIENTE'] },
        loadChildren: () =>
          import('./modules/permissions/permissions.module')
            .then(m => m.PermissionsModule)
      },
      {
        path: 'bitacora',
        canActivate: [AuthGuard, RoleGuard],
        data: { rolesExcluidos: ['CLIENTE'] },
        loadChildren: () =>
          import('./modules/bitacora/bitacora.module')
            .then(m => m.BitacoraModule)
      },
      {
        path: 'clients',
        canActivate: [AuthGuard, RoleGuard],
        data: { rolesExcluidos: ['CLIENTE'] },
        loadChildren: () =>
          import('./modules/clients/clients.module')
            .then(m => m.ClientsModule)
      },
      {
        path: 'attributes',
        canActivate: [AuthGuard, RoleGuard],
        data: { rolesExcluidos: ['CLIENTE'] },
        loadChildren: () =>
          import('./modules/attributes/attributes.module')
            .then(m => m.AttributesModule)
      },
      {
        path: 'products',
        canActivate: [AuthGuard, RoleGuard],
        data: { rolesExcluidos: ['CLIENTE'] },
        loadChildren: () =>
          import('./modules/products/products.module')
            .then(m => m.ProductsModule)
      },
      {
        path: 'reservations',
        canActivate: [AuthGuard],
        loadChildren: () =>
          import('./modules/reservations/reservations.module')
            .then(m => m.ReservationsModule)
      },
      {
        path: 'profile',
        canActivate: [AuthGuard],
        loadChildren: () =>
          import('./modules/profile/profile.module')
            .then(m => m.ProfileModule)
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
export class AppRoutingModule { }