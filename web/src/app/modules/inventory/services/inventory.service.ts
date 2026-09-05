import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { StockItem, InventoryMovement } from '../../../core/models/inventory.interface';

@Injectable({
  providedIn: 'root'
})
export class InventoryService {
  constructor(private apiService: ApiService) {}

  getStockItems(): Observable<any> {
    return this.apiService.get('/inventory/stock/');
  }

  getMovements(): Observable<any> {
    return this.apiService.get('/inventory/movimientos/');
  }

  registerMovement(data: any): Observable<InventoryMovement> {
    return this.apiService.post('/inventory/movimientos/registrar/', data);
  }
}