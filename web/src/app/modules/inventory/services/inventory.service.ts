// web/src/app/modules/inventory/services/inventory.service.ts

import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { StockItem, InventoryMovement } from '../../../core/models/inventory.interface';

@Injectable({
  providedIn: 'root'
})
export class InventoryService {
  constructor(private apiService: ApiService) {}


  getStockItems(varianteId?: number): Observable<any> {
    const params: any = { page_size: 50 };
    if (varianteId) {
      params.variante = varianteId;
    }
    return this.apiService.get<StockItem[]>('/inventory/stock/', params);
  }

  getMovements(): Observable<any> {
    return this.apiService.get('/inventory/movimientos/');
  }

  registerMovement(data: any): Observable<InventoryMovement> {
    return this.apiService.post('/inventory/movimientos/registrar/', data);
  }

  getSucursales(): Observable<any> {
    return this.apiService.get('/catalog/sucursales/');
  }

  getVariantes(busqueda?: string): Observable<any> {
    const params: any = { page_size: 50 };
    if (busqueda) {
      params.busqueda = busqueda;
    }
    return this.apiService.get('/catalog/variantes/', params);
  }
}