// web/src/app/modules/reservations/pages/reservation-list/reservation-list.component.ts
//
// Archivo NUEVO (estaba vacío). Sirve tanto para CU12 (encargado ve
// todas las reservas, con nombre de cliente, y puede confirmar/
// completar/cancelar) como CU13 (cliente ve solo las suyas y puede
// cancelar) - el backend ya filtra el queryset según el rol, aquí solo
// se decide qué botones mostrar.

import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../../../core/auth/auth.service';
import { ReservationService } from '../../services/reservation.service';

@Component({
  selector: 'app-reservation-list',
  templateUrl: './reservation-list.component.html',
  styleUrls: ['./reservation-list.component.scss']
})
export class ReservationListComponent implements OnInit {
  reservas: any[] = [];
  loading = false;
  esEncargado = false;
  actionError = '';

  constructor(
    private reservationService: ReservationService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    const roles = this.authService.obtenerRoles();
    this.esEncargado = roles.some(r =>
      ['SUPER_ADMIN', 'ADMIN_EMPRESA', 'ENCARGADO_SUCURSAL'].includes(r)
    );
    this.cargarReservas();
  }

  cargarReservas(): void {
    this.loading = true;
    this.reservationService.getReservas().subscribe({
      next: (data: any) => {
        this.reservas = data.results || data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  cancelar(id: number): void {
    this.actionError = '';
    this.reservationService.cancelarReserva(id).subscribe({
      next: () => this.cargarReservas(),
      error: (err) => {
        this.actionError = err?.error?.error || 'No se pudo cancelar la reserva.';
      }
    });
  }

  confirmar(id: number): void {
    this.reservationService.confirmarReserva(id).subscribe({
      next: () => this.cargarReservas()
    });
  }

  completar(id: number): void {
    this.reservationService.completarReserva(id).subscribe({
      next: () => this.cargarReservas()
    });
  }

  puedeCancelar(reserva: any): boolean {
    return reserva.estado === 'PENDIENTE' || reserva.estado === 'CONFIRMADA';
  }
}