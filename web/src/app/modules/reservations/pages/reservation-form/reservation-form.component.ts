// web/src/app/modules/reservations/pages/reservations-form/reservation-form.component.ts
//
// Archivo NUEVO (estaba vacío). Permite al cliente elegir sucursal,
// fecha/hora, e ir agregando varias prendas (producto+variante) antes
// de enviar la reserva - consume POST /reservations/reservas/, que ahora
// acepta "items" (varias variantes por reserva).

import { Component, OnInit } from '@angular/core';
import { CatalogService } from '../../../catalog/services/catalog.service';
import { ReservationService } from '../../services/reservation.service';

interface ReservationItem {
  id_variante: number;
  label: string;
}

@Component({
  selector: 'app-reservation-form',
  templateUrl: './reservation-form.component.html',
  styleUrls: ['./reservation-form.component.scss']
})
export class ReservationFormComponent implements OnInit {
  products: any[] = [];
  sucursales: any[] = [];

  selectedProductId: number | null = null;
  selectedVarianteId: number | null = null;
  selectedSucursalId: number | null = null;
  fechaReserva: string = '';
  horaReserva: string = '';

  items: ReservationItem[] = [];

  loading = false;
  submitting = false;
  errorMessage = '';
  successMessage = '';

  constructor(
    private catalogService: CatalogService,
    private reservationService: ReservationService
  ) {}

  ngOnInit(): void {
    this.loading = true;
    this.catalogService.getProducts().subscribe({
      next: (data: any) => {
        this.products = data.results || data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
    this.catalogService.getBranches().subscribe({
      next: (data: any) => {
        this.sucursales = data.results || data;
      },
      error: () => {}
    });
  }

  get selectedProduct(): any {
    return this.products.find(p => p.id_producto === Number(this.selectedProductId));
  }

  addItem(): void {
    this.errorMessage = '';
    const producto = this.selectedProduct;
    if (!producto || !this.selectedVarianteId) {
      this.errorMessage = 'Selecciona un producto y una variante antes de agregar.';
      return;
    }
    const variante = (producto.variantes || []).find(
      (v: any) => v.id_variante === Number(this.selectedVarianteId)
    );
    if (!variante) {
      return;
    }
    const yaAgregada = this.items.some(i => i.id_variante === variante.id_variante);
    if (yaAgregada) {
      this.errorMessage = 'Esa prenda ya está en la reserva.';
      return;
    }
    this.items.push({
      id_variante: variante.id_variante,
      label: `${producto.nombre} - ${variante.talla?.nombre} - ${variante.color?.nombre}`
    });
    this.selectedVarianteId = null;
  }

  removeItem(index: number): void {
    this.items.splice(index, 1);
  }

  submit(): void {
    this.errorMessage = '';
    this.successMessage = '';

    if (!this.selectedSucursalId) {
      this.errorMessage = 'Selecciona una sucursal.';
      return;
    }
    if (!this.fechaReserva || !this.horaReserva) {
      this.errorMessage = 'Selecciona fecha y hora.';
      return;
    }
    if (this.items.length === 0) {
      this.errorMessage = 'Agrega al menos una prenda a la reserva.';
      return;
    }

    const payload = {
      id_sucursal: this.selectedSucursalId,
      fecha_reserva: this.fechaReserva,
      hora_reserva: this.horaReserva,
      items: this.items.map(i => ({ id_variante: i.id_variante }))
    };

    this.submitting = true;
    this.reservationService.crearReserva(payload).subscribe({
      next: () => {
        this.submitting = false;
        this.successMessage = 'Reserva creada correctamente. Te esperamos en la sucursal elegida.';
        this.items = [];
        this.selectedSucursalId = null;
        this.fechaReserva = '';
        this.horaReserva = '';
      },
      error: (err) => {
        this.submitting = false;
        this.errorMessage = err?.error?.detail || 'No se pudo crear la reserva. Intenta nuevamente.';
      }
    });
  }
}