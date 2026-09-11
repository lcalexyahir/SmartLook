// web/src/app/modules/attributes/services/attribute.service.ts
//
// Archivo YA EXISTENTE. Se agregan CRUD de Categoría, Marca, Temporada
// y Colección (CU04). Tallas/Colores quedan igual.

import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

@Injectable({
  providedIn: 'root'
})
export class AttributeService {
  constructor(private apiService: ApiService) {}

  // ---- Tallas ----
  getTallas(): Observable<any> { return this.apiService.get('/catalog/tallas/'); }
  crearTalla(data: any): Observable<any> { return this.apiService.post('/catalog/tallas/', data); }
  actualizarTalla(id: number, data: any): Observable<any> { return this.apiService.patch(`/catalog/tallas/${id}/`, data); }
  eliminarTalla(id: number): Observable<any> { return this.apiService.delete(`/catalog/tallas/${id}/`); }

  // ---- Colores ----
  getColores(): Observable<any> { return this.apiService.get('/catalog/colores/'); }
  crearColor(data: any): Observable<any> { return this.apiService.post('/catalog/colores/', data); }
  actualizarColor(id: number, data: any): Observable<any> { return this.apiService.patch(`/catalog/colores/${id}/`, data); }
  eliminarColor(id: number): Observable<any> { return this.apiService.delete(`/catalog/colores/${id}/`); }

  // ---- Categorías ----
  getCategorias(): Observable<any> { return this.apiService.get('/catalog/categorias/'); }
  crearCategoria(data: any): Observable<any> { return this.apiService.post('/catalog/categorias/', data); }
  actualizarCategoria(id: number, data: any): Observable<any> { return this.apiService.patch(`/catalog/categorias/${id}/`, data); }
  eliminarCategoria(id: number): Observable<any> { return this.apiService.delete(`/catalog/categorias/${id}/`); }

  // ---- Marcas ----
  getMarcas(): Observable<any> { return this.apiService.get('/catalog/marcas/'); }
  crearMarca(data: any): Observable<any> { return this.apiService.post('/catalog/marcas/', data); }
  actualizarMarca(id: number, data: any): Observable<any> { return this.apiService.patch(`/catalog/marcas/${id}/`, data); }
  eliminarMarca(id: number): Observable<any> { return this.apiService.delete(`/catalog/marcas/${id}/`); }

  // ---- Temporadas ----
  getTemporadas(): Observable<any> { return this.apiService.get('/catalog/temporadas/'); }
  crearTemporada(data: any): Observable<any> { return this.apiService.post('/catalog/temporadas/', data); }
  actualizarTemporada(id: number, data: any): Observable<any> { return this.apiService.patch(`/catalog/temporadas/${id}/`, data); }
  eliminarTemporada(id: number): Observable<any> { return this.apiService.delete(`/catalog/temporadas/${id}/`); }

  // ---- Colecciones ----
  getColecciones(): Observable<any> { return this.apiService.get('/catalog/colecciones/'); }
  crearColeccion(data: any): Observable<any> { return this.apiService.post('/catalog/colecciones/', data); }
  actualizarColeccion(id: number, data: any): Observable<any> { return this.apiService.patch(`/catalog/colecciones/${id}/`, data); }
  eliminarColeccion(id: number): Observable<any> { return this.apiService.delete(`/catalog/colecciones/${id}/`); }
}