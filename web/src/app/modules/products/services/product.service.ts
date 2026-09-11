// web/src/app/modules/products/services/product.service.ts
//
// Archivo YA EXISTENTE. Se agrega CRUD de variantes (Paso C).
// getProductos/crearProducto/actualizarProducto/eliminarProducto
// quedan igual.

import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

@Injectable({
  providedIn: 'root'
})
export class ProductService {
  constructor(private apiService: ApiService) {}

  getProductos(): Observable<any> {
    return this.apiService.get('/catalog/productos/');
  }

  crearProducto(data: any): Observable<any> {
    return this.apiService.post('/catalog/productos/', data);
  }

  actualizarProducto(id: number, data: any): Observable<any> {
    return this.apiService.patch(`/catalog/productos/${id}/`, data);
  }

  eliminarProducto(id: number): Observable<any> {
    return this.apiService.delete(`/catalog/productos/${id}/`);
  }

  crearVariante(data: any): Observable<any> {
    return this.apiService.post('/catalog/variantes/', data);
  }

  actualizarVariante(id: number, data: any): Observable<any> {
    return this.apiService.patch(`/catalog/variantes/${id}/`, data);
  }

  eliminarVariante(id: number): Observable<any> {
    return this.apiService.delete(`/catalog/variantes/${id}/`);
  }
}