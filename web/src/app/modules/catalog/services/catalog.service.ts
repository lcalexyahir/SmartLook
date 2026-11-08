// web/src/app/modules/catalog/services/catalog.service.ts
//
// MODIFICADO (corrección catálogo de 20 prendas): la API entrega los productos
// por páginas (20 por defecto) y el catálogo solo leía la primera. Ahora, si
// quien llama no pide un tamaño de página (como la portada pública, que
// muestra solo unos cuantos), se leen todas las páginas.
import { Injectable } from '@angular/core';
import { EMPTY, Observable } from 'rxjs';
import { expand, map, reduce } from 'rxjs/operators';
import { ApiService } from '../../../core/services/api.service';
import { Product, Category, Brand, Size, Color, Branch, Supplier } from '../../../core/models/product.interface';

@Injectable({
  providedIn: 'root'
})
export class CatalogService {
  constructor(private apiService: ApiService) {}

  getProducts(filters?: any): Observable<any> {
    // Con page_size explícito se respeta (una sola página).
    if (filters?.page_size) {
      return this.apiService.get('/catalog/productos/', filters);
    }
    const pedir = (pagina: number) =>
      this.apiService.get<any>('/catalog/productos/', { ...filters, page_size: 100, page: pagina });
    return pedir(1).pipe(
      expand((respuesta, indice) => (respuesta?.next ? pedir(indice + 2) : EMPTY)),
      map(respuesta => (respuesta?.results ?? respuesta ?? []) as any[]),
      reduce((todos, pagina) => todos.concat(pagina), [] as any[])
    );
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