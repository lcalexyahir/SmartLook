import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

@Injectable({
  providedIn: 'root'
})
export class ReservationService {
  constructor(private apiService: ApiService) {}

  crearReserva(data: any): Observable<any> {
    return this.apiService.post('/reservations/reservas/', data);
  }

  getReservas(): Observable<any> {
    return this.apiService.get('/reservations/reservas/');
  }

  cancelarReserva(id: number): Observable<any> {
    return this.apiService.post(`/reservations/reservas/${id}/cancelar/`, {});
  }

  confirmarReserva(id: number): Observable<any> {
    return this.apiService.post(`/reservations/reservas/${id}/confirmar/`, {});
  }

  completarReserva(id: number): Observable<any> {
    return this.apiService.post(`/reservations/reservas/${id}/completar/`, {});
  }
}