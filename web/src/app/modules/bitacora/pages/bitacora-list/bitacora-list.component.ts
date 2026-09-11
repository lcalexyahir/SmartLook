// web/src/app/modules/bitacora/pages/bitacora-list/bitacora-list.component.ts
//
// Archivo NUEVO. Solo lectura: la bitácora nunca se edita ni se borra
// desde la UI, es un registro de auditoría.

import { Component, OnInit } from '@angular/core';
import { UserService } from '../../../../core/services/user.service';

@Component({
  selector: 'app-bitacora-list',
  templateUrl: './bitacora-list.component.html',
  styleUrls: ['./bitacora-list.component.scss']
})
export class BitacoraListComponent implements OnInit {
  eventos: any[] = [];
  loading = false;
  filtroAccion = '';

  constructor(private userService: UserService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading = true;
    this.userService.getBitacora().subscribe({
      next: (data) => {
        this.eventos = data;
        this.loading = false;
      },
      error: () => {
        this.eventos = [];
        this.loading = false;
      }
    });
  }

  get eventosFiltrados(): any[] {
    if (!this.filtroAccion) return this.eventos;
    return this.eventos.filter(
      e => e.accion?.toLowerCase().includes(this.filtroAccion.toLowerCase())
    );
  }
}