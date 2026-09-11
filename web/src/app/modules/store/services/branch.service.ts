// web/src/app/modules/store/services/branch.service.ts
//
// Archivo YA EXISTENTE. Se agregan updateBranch usage ya existía; se
// agregan createCity/updateCity/deleteCity (CU06 - Ciudades).
// getCountries/getCities/getBranches/createBranch/updateBranch quedan
// igual.

import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { Country, City, Branch } from '../../../core/models/branch.interface';

@Injectable({
  providedIn: 'root'
})
export class BranchService {
  constructor(private apiService: ApiService) {}

  getCountries(): Observable<any> {
    return this.apiService.get('/catalog/paises/');
  }

  getCities(): Observable<any> {
    return this.apiService.get('/catalog/ciudades/');
  }

  getBranches(): Observable<any> {
    return this.apiService.get('/catalog/sucursales/');
  }

  createBranch(data: any): Observable<Branch> {
    return this.apiService.post('/catalog/sucursales/', data);
  }

  updateBranch(id: number, data: any): Observable<Branch> {
    return this.apiService.put(`/catalog/sucursales/${id}/`, data);
  }

  deleteBranch(id: number): Observable<any> {
    return this.apiService.delete(`/catalog/sucursales/${id}/`);
  }

  createCity(data: any): Observable<City> {
    return this.apiService.post('/catalog/ciudades/', data);
  }

  updateCity(id: number, data: any): Observable<City> {
    return this.apiService.put(`/catalog/ciudades/${id}/`, data);
  }

  deleteCity(id: number): Observable<any> {
    return this.apiService.delete(`/catalog/ciudades/${id}/`);
  }
}