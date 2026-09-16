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
    return this.apiService.get<StockItem[]>('/inventory/stock/', { variante: varianteId });
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

  // NUEVO (CU16): parámetro opcional de búsqueda para el mostrador de caja.
  getVariantes(busqueda?: string): Observable<any> {
    return this.apiService.get('/catalog/variantes/', busqueda ? { busqueda } : {});
  }
}