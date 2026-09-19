import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

export interface DatosEntrega {
  direccion: string;
  referencia?: string;
  latitud: number;
  longitud: number;
}

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

  // CU21: cotiza el envío a domicilio (distancia y costo) para el carrito actual.
  cotizarEnvio(idSucursal: number, latitud: number, longitud: number): Observable<any> {
    return this.apiService.post('/sales/carritos/cotizar-envio/', {
      id_sucursal: idSucursal,
      latitud,
      longitud
    });
  }

  // CU21: sin "entrega" es retiro en sucursal; con "entrega" es delivery.
  checkout(idSucursal: number, entrega?: DatosEntrega): Observable<any> {
    const body: any = {
      id_sucursal: idSucursal,
      tipo_entrega: entrega ? 'DELIVERY' : 'RETIRO'
    };
    if (entrega) {
      body.direccion = entrega.direccion;
      body.referencia = entrega.referencia || '';
      body.latitud = entrega.latitud;
      body.longitud = entrega.longitud;
    }
    return this.apiService.post('/sales/carritos/checkout/', body);
  }

  confirmarPago(referenciaPago: string): Observable<any> {
    return this.apiService.post('/sales/carritos/confirmar_pago/', { referencia_pago: referenciaPago });
  }
}