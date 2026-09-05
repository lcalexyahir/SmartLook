import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { Supplier } from '../../../core/models/branch.interface';

@Injectable({
  providedIn: 'root'
})
export class SupplierService {
  constructor(private apiService: ApiService) {}

  getSuppliers(): Observable<any> {
    return this.apiService.get('/catalog/proveedores/');
  }

  createSupplier(data: any): Observable<Supplier> {
    return this.apiService.post('/catalog/proveedores/', data);
  }

  updateSupplier(id: number, data: any): Observable<Supplier> {
    return this.apiService.put(`/catalog/proveedores/${id}/`, data);
  }

  deleteSupplier(id: number): Observable<any> {
    return this.apiService.delete(`/catalog/proveedores/${id}/`);
  }
}