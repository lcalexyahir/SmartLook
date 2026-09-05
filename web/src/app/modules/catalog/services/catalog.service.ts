import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { Product, Category, Brand, Size, Color, Branch, Supplier } from '../../../core/models/product.interface';

@Injectable({
  providedIn: 'root'
})
export class CatalogService {
  constructor(private apiService: ApiService) {}

  getProducts(filters?: any): Observable<any> {
    return this.apiService.get('/catalog/productos/', filters);
  }

  getProduct(id: number): Observable<Product> {
    return this.apiService.get(`/catalog/productos/${id}/`);
  }

  getCategories(): Observable<Category[]> {
    return this.apiService.get('/catalog/categorias/');
  }

  getBrands(): Observable<Brand[]> {
    return this.apiService.get('/catalog/marcas/');
  }

  getSizes(): Observable<Size[]> {
    return this.apiService.get('/catalog/tallas/');
  }

  getColors(): Observable<Color[]> {
    return this.apiService.get('/catalog/colores/');
  }

  getBranches(): Observable<Branch[]> {
    return this.apiService.get('/catalog/sucursales/');
  }

  getSuppliers(): Observable<Supplier[]> {
    return this.apiService.get('/catalog/proveedores/');
  }

  createProduct(data: any): Observable<Product> {
    return this.apiService.post('/catalog/productos/', data);
  }

  updateProduct(id: number, data: any): Observable<Product> {
    return this.apiService.put(`/catalog/productos/${id}/`, data);
  }

  deleteProduct(id: number): Observable<any> {
    return this.apiService.delete(`/catalog/productos/${id}/`);
  }
}