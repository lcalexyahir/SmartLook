// web/src/app/core/auth/role.guard.ts
//
// Archivo NUEVO. Complementa a auth_guard.ts (ese verifica que haya
// sesión; este verifica que el rol tenga permitido entrar a la ruta).
//
// Uso en app-routing.module.ts:
//   canActivate: [AuthGuard, RoleGuard],
//   data: { rolesExcluidos: ['CLIENTE'] }

import { Injectable } from '@angular/core';
import { CanActivate, Router, ActivatedRouteSnapshot } from '@angular/router';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class RoleGuard implements CanActivate {

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(route: ActivatedRouteSnapshot): boolean {

    const rolesExcluidos: string[] = route.data['rolesExcluidos'] ?? [];
    const rolesUsuario = this.authService.obtenerRoles();

    const tieneRolExcluido = rolesUsuario.some(
      rol => rolesExcluidos.includes(rol)
    );

    if (tieneRolExcluido) {
      // Un CLIENTE que intenta entrar a una vista administrativa
      // se manda a su propia vista (catálogo), no al login.
      this.router.navigate(['/catalog']);
      return false;
    }

    return true;

  }

}