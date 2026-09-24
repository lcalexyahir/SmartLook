// web/src/app/modules/devoluciones/pages/devoluciones-list/devoluciones-list.component.ts
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../../../core/services/api.service';

@Component({
  selector: 'app-devoluciones-list',
  templateUrl: './devoluciones-list.component.html',
  styleUrls: ['./devoluciones-list.component.scss']
})
export class DevolucionesListComponent implements OnInit {
  devoluciones: any[] = [];
  sucursales: any[] = [];
  sucursalSeleccionada: string = '';
  loading = false;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargarSucursales();
    this.cargarDevoluciones();
  }

  cargarSucursales(): void {
    this.api.get<any>('/catalog/sucursales/').subscribe({
      next: (data: any) => this.sucursales = data.results || data,
      error: () => this.sucursales = []
    });
  }

  cargarDevoluciones(): void {
    this.loading = true;
    const params: any = {};
    if (this.sucursalSeleccionada) {
      params.sucursal = this.sucursalSeleccionada;
    }
    this.api.get<any>('/sales/devoluciones/', params).subscribe({
      next: (data: any) => {
        this.devoluciones = data.results || data;
        this.loading = false;
      },
      error: () => {
        this.devoluciones = [];
        this.loading = false;
      }
    });
  }

  onFiltroSucursal(): void {
    this.cargarDevoluciones();
  }
}