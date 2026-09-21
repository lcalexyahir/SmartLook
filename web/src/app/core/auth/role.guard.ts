// web/src/app/core/auth/role.guard.ts
// CU21: un usuario cuyo único rol operativo es REPARTIDOR solo puede entrar a
// las rutas marcadas con data: { permitirRepartidor: true } (Entregas).
import { Injectable } from '@angular/core';
import { CanActivate, Router, ActivatedRouteSnapshot } from '@angular/router';
import { AuthService } from './auth.service';

const ROLES_PERSONAL = ['SUPER_ADMIN', 'ADMIN_EMPRESA', 'ENCARGADO_SUCURSAL', 'CAJERO'];

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

    const esSoloRepartidor =
      rolesUsuario.includes('REPARTIDOR') &&
      !rolesUsuario.some(rol => ROLES_PERSONAL.includes(rol));

    if (esSoloRepartidor && !route.data['permitirRepartidor']) {
      // Un repartidor que intenta entrar a una pantalla administrativa
      // se manda a su propia vista (Entregas).
      this.router.navigate(['/deliveries']);
      return false;
    }

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