// web/src/app/modules/inventory/services/inventory.service.ts
//
// Archivo YA EXISTENTE. getStockItems() ahora acepta un varianteId
// opcional para CU08 (consulta de disponibilidad del cliente).
// getMovements(), registerMovement(), getSucursales() y getVariantes()
// quedan igual.

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

  getVariantes(): Observable<any> {
    return this.apiService.get('/catalog/variantes/');
  }
}