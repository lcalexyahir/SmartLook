// web/src/app/modules/pos/services/pos-sale.service.ts

import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

@Injectable({
  providedIn: 'root'
})
export class PosSaleService {
  constructor(private apiService: ApiService) {}

  registrarVenta(idSucursal: number, metodoPago: string, items: { id_variante: number; cantidad: number }[]): Observable<any> {
    return this.apiService.post('/sales/ventas-pos/registrar/', {
      id_sucursal: idSucursal,
      metodo_pago: metodoPago,
      items,
    });
  }
}