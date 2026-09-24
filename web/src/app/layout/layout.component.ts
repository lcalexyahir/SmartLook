// web/src/app/layout/layout.component.ts
//
// CU21: además de esCliente, expone esPersonal (administración/tienda),
// esSoloRepartidor y puedeVerEntregas, para que la plantilla muestre a cada
// rol solamente su propio menú.
// MODIFICADO (CU20): se agrega puedeVerAsistente (asistente de gestión).
// NUEVO (devoluciones): se agrega puedeVerDevoluciones.

import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../core/auth/auth.service';

const ROLES_PERSONAL = ['SUPER_ADMIN', 'ADMIN_EMPRESA', 'ENCARGADO_SUCURSAL', 'CAJERO'];
const ROLES_ENTREGAS = ['SUPER_ADMIN', 'ADMIN_EMPRESA', 'ENCARGADO_SUCURSAL', 'REPARTIDOR'];
const ROLES_ASISTENTE = ['SUPER_ADMIN', 'ADMIN_EMPRESA', 'ENCARGADO_SUCURSAL'];
const ROLES_DEVOLUCIONES = ['SUPER_ADMIN', 'ADMIN_EMPRESA', 'ENCARGADO_SUCURSAL'];

@Component({
  selector: 'app-layout',
  templateUrl: './layout.component.html',
  styleUrls: ['./layout.component.css']
})
export class LayoutComponent {
  usuario: any = null;
  esCliente = false;
  esSoloRepartidor = false;
  esPersonal = false;
  puedeVerEntregas = false;
  puedeVerAsistente = false;
  puedeVerDevoluciones = false;
  sidebarVisible = true;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {
    const data = localStorage.getItem('usuario');
    if (data) {
      this.usuario = JSON.parse(data);
    }
    const roles = this.authService.obtenerRoles();
    this.esCliente = this.authService.esCliente();
    this.esSoloRepartidor =
      roles.includes('REPARTIDOR') && !roles.some(rol => ROLES_PERSONAL.includes(rol));
    this.esPersonal = !this.esCliente && !this.esSoloRepartidor;
    this.puedeVerEntregas = roles.some(rol => ROLES_ENTREGAS.includes(rol));
    this.puedeVerAsistente = roles.some(rol => ROLES_ASISTENTE.includes(rol));
    this.puedeVerDevoluciones = roles.some(rol => ROLES_DEVOLUCIONES.includes(rol));
  }

  cerrarSesion(): void {
    this.authService.logout();
  }
}