import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

@Injectable({
  providedIn: 'root'
})
export class CartService {
  constructor(private apiService: ApiService) {}

  getCarritoActual(): Observable<any> {
    return this.apiService.get('/sales/carritos/actual/');
  }

  agregarItem(idVariante: number, cantidad: number = 1): Observable<any> {
    return this.apiService.post('/sales/carrito-items/', {
      id_variante: idVariante,
      cantidad
    });
  }

  actualizarCantidad(idItem: number, cantidad: number): Observable<any> {
    return this.apiService.patch(`/sales/carrito-items/${idItem}/`, { cantidad });
  }

  quitarItem(idItem: number): Observable<any> {
    return this.apiService.delete(`/sales/carrito-items/${idItem}/`);
  }
}