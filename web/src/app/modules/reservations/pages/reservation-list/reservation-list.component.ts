// web/src/app/modules/reservations/pages/reservation-list/reservation-list.component.ts
//
// Archivo NUEVO (estaba vacío). Sirve tanto para CU12 (encargado ve
// todas las reservas, con nombre de cliente, y puede confirmar/
// completar/cancelar) como CU13 (cliente ve solo las suyas y puede
// cancelar) - el backend ya filtra el queryset según el rol, aquí solo
// se decide qué botones mostrar.
// MODIFICADO (SaaS - A.5): el cliente ve también sus reservas hechas sin
// conexión con su estado (Registrada localmente, Enviada, Confirmada,
// Rechazada), puede sincronizarlas, descartar las rechazadas y quitar las
// confirmadas. Sin conexión, la lista del servidor sale de la copia guardada.
import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import { AuthService } from '../../../../core/auth/auth.service';
import { ConexionService } from '../../../../core/services/conexion.service';
import { ReservationService } from '../../services/reservation.service';
import {
  ReservaLocal,
  ReservaOfflineService,
  ResultadoSyncReservas
} from '../../services/reserva-offline.service';

@Component({
  selector: 'app-reservation-list',
  templateUrl: './reservation-list.component.html',
  styleUrls: ['./reservation-list.component.scss']
})
export class ReservationListComponent implements OnInit, OnDestroy {
  reservas: any[] = [];
  loading = false;
  esEncargado = false;
  actionError = '';
  // NUEVO (A.5)
  enLinea = true;
  reservasLocales: ReservaLocal[] = [];
  sincronizando = false;
  resultadoSync: ResultadoSyncReservas | null = null;
  sinDatosGuardados = false;
  private suscripciones = new Subscription();

  constructor(
    private reservationService: ReservationService,
    private authService: AuthService,
    private reservaOffline: ReservaOfflineService,
    private conexion: ConexionService
  ) {}

  ngOnInit(): void {
    const roles = this.authService.obtenerRoles();
    this.esEncargado = roles.some(r =>
      ['SUPER_ADMIN', 'ADMIN_EMPRESA', 'ENCARGADO_SUCURSAL'].includes(r)
    );
    this.suscripciones.add(this.conexion.enLinea$.subscribe(enLinea => this.enLinea = enLinea));
    if (!this.esEncargado) {
      this.suscripciones.add(this.reservaOffline.reservas$.subscribe(r => this.reservasLocales = r));
      this.suscripciones.add(this.reservaOffline.sincronizando$.subscribe(s => this.sincronizando = s));
      this.suscripciones.add(this.reservaOffline.resultado$.subscribe(resultado => {
        const nuevas = !!resultado && resultado !== this.resultadoSync &&
          resultado.sincronizadas + resultado.duplicadas > 0;
        this.resultadoSync = resultado;
        // Las reservas confirmadas ya aparecen en la lista del servidor.
        if (nuevas) {
          this.cargarReservas();
        }
      }));
      this.reservaOffline.recargar();
      this.reservaOffline.sincronizar();
    }
    this.cargarReservas();
  }

  ngOnDestroy(): void {
    this.suscripciones.unsubscribe();
  }

  get pendientes(): number {
    return this.reservasLocales.filter(r => r.estado === 'REGISTRADA' || r.estado === 'ENVIADA').length;
  }

  get confirmadas(): number {
    return this.reservasLocales.filter(r => r.estado === 'CONFIRMADA').length;
  }

  get rechazadas(): number {
    return this.reservasLocales.filter(r => r.estado === 'RECHAZADA').length;
  }

  cargarReservas(): void {
    this.loading = true;
    this.sinDatosGuardados = false;
    this.reservationService.getReservas().subscribe({
      next: (data: any) => {
        this.reservas = data.results || data;
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.sinDatosGuardados = this.conexion.esErrorDeRed(err);
      }
    });
  }

  cancelar(id: number): void {
    this.actionError = '';
    this.reservationService.cancelarReserva(id).subscribe({
      next: () => this.cargarReservas(),
      error: (err) => {
        this.actionError = this.conexion.esErrorDeRed(err)
          ? 'Sin conexión: la reserva no se puede cancelar ahora. Inténtalo al recuperar internet.'
          : err?.error?.error || 'No se pudo cancelar la reserva.';
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

  // ---------------------------------------------------------------- reservas sin conexión
  sincronizarAhora(): void {
    this.reservaOffline.sincronizar();
  }

  descartar(reserva: ReservaLocal): void {
    if (confirm('¿Descartar esta reserva rechazada? Se borrará de este dispositivo.')) {
      this.reservaOffline.descartar(reserva);
    }
  }

  limpiarConfirmadas(): void {
    this.reservaOffline.limpiarConfirmadas();
  }

  prendas(reserva: ReservaLocal): string {
    return reserva.items.map(i => i.label).join(', ');
  }

  textoEstado(reserva: ReservaLocal): string {
    switch (reserva.estado) {
      case 'CONFIRMADA':
        return reserva.id_reserva ? `Confirmada · Reserva #${reserva.id_reserva}` : 'Confirmada';
      case 'RECHAZADA':
        return 'Rechazada';
      case 'ENVIADA':
        return 'Enviada';
      default:
        return 'Registrada localmente';
    }
  }
}