// web/src/app/modules/clients/pages/client-list/client-list.component.ts
//
// Archivo NUEVO. Solo lectura: el admin no crea clientes (se registran
// ellos mismos, CU01), esta pantalla solo permite consultarlos.

import { Component, OnInit } from '@angular/core';
import { UserService } from '../../../../core/services/user.service';

@Component({
  selector: 'app-client-list',
  templateUrl: './client-list.component.html',
  styleUrls: ['./client-list.component.scss']
})
export class ClientListComponent implements OnInit {
  clientes: any[] = [];
  loading = false;
  busqueda = '';

  constructor(private userService: UserService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading = true;
    this.userService.getClientes().subscribe({
      next: (data) => {
        this.clientes = data;
        this.loading = false;
      },
      error: () => {
        this.clientes = [];
        this.loading = false;
      }
    });
  }

  get clientesFiltrados(): any[] {
    if (!this.busqueda) return this.clientes;
    const termino = this.busqueda.toLowerCase();
    return this.clientes.filter(c =>
      `${c.nombres} ${c.apellidos}`.toLowerCase().includes(termino) ||
      c.correo.toLowerCase().includes(termino)
    );
  }
}