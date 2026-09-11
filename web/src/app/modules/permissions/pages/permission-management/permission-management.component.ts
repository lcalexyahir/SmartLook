// web/src/app/modules/permissions/pages/permission-management/permission-management.component.ts
//
// Archivo NUEVO.

import { Component, OnInit } from '@angular/core';
import { UserService } from '../../../../core/services/user.service';
import { Role, Permiso } from '../../../../core/models/user.interface';

@Component({
  selector: 'app-permission-management',
  templateUrl: './permission-management.component.html',
  styleUrls: ['./permission-management.component.scss']
})
export class PermissionManagementComponent implements OnInit {
  roles: Role[] = [];
  permisos: Permiso[] = [];
  idRolSeleccionado: number | null = null;
  idsPermisosAsignados: Set<number> = new Set();
  loading = false;
  guardando = false;
  errorMessage: string | null = null;
  successMessage: string | null = null;

  constructor(private userService: UserService) {}

  ngOnInit(): void {
    // A diferencia de "Usuarios y Roles", aquí SÍ se incluye el rol
    // CLIENTE: sus permisos también se gestionan desde este panel,
    // aunque los clientes se registren solos (CU01) y no se creen aquí.
    this.userService.getRoles().subscribe({
      next: (data) => this.roles = data,
      error: () => this.roles = []
    });

    this.userService.getPermisos().subscribe({
      next: (data) => this.permisos = data,
      error: () => this.permisos = []
    });
  }

  seleccionarRol(idRol: number): void {
    this.idRolSeleccionado = idRol;
    this.errorMessage = null;
    this.successMessage = null;
    this.loading = true;

    this.userService.getRolPermisos(idRol).subscribe({
      next: (resp) => {
        this.idsPermisosAsignados = new Set(resp.permisos);
        this.loading = false;
      },
      error: () => {
        this.idsPermisosAsignados = new Set();
        this.loading = false;
      }
    });
  }

  estaAsignado(idPermiso: number): boolean {
    return this.idsPermisosAsignados.has(idPermiso);
  }

  toggle(idPermiso: number): void {
    if (this.idsPermisosAsignados.has(idPermiso)) {
      this.idsPermisosAsignados.delete(idPermiso);
    } else {
      this.idsPermisosAsignados.add(idPermiso);
    }
  }

  guardar(): void {
    if (this.idRolSeleccionado === null) return;

    this.guardando = true;
    this.errorMessage = null;
    this.successMessage = null;

    const permisos = Array.from(this.idsPermisosAsignados);

    this.userService.actualizarRolPermisos(this.idRolSeleccionado, permisos).subscribe({
      next: () => {
        this.guardando = false;
        this.successMessage = 'Permisos actualizados correctamente.';
      },
      error: () => {
        this.guardando = false;
        this.errorMessage = 'No se pudieron guardar los permisos.';
      }
    });
  }
}