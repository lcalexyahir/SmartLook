// web/src/app/core/services/user.service.ts
//
// Archivo YA EXISTENTE. Se agrega getClientes(). El resto del archivo
// (getUsuarios, getRoles, crearUsuario, actualizarUsuario, eliminarUsuario,
// getPermisos, getRolPermisos, actualizarRolPermisos, getBitacora) queda
// igual.

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class UserService {

  private apiUrl = 'http://127.0.0.1:8000/api/auth';

  constructor(
    private http: HttpClient
  ) {}

  getUsuarios(): Observable<any[]> {

    return this.http.get<any>(
      `${this.apiUrl}/usuarios/`
    ).pipe(

      map(response => {

        return response.results ?? response;

      })

    );

  }

  getRoles(): Observable<any[]> {

    return this.http.get<any>(
      `${this.apiUrl}/roles/`
    ).pipe(

      map(response => {

        return response.results ?? response;

      })

    );

  }


  crearUsuario(data:any): Observable<any>{

    return this.http.post<any>(
      `${this.apiUrl}/usuarios/`,
      data
    );

  }


  actualizarUsuario(id: number, data: any): Observable<any> {

    return this.http.patch<any>(
      `${this.apiUrl}/usuarios/${id}/`,
      data
    );

  }


  eliminarUsuario(id: number): Observable<any> {

    return this.http.delete<any>(
      `${this.apiUrl}/usuarios/${id}/`
    );

  }


  getPermisos(): Observable<any[]> {

    return this.http.get<any>(
      `${this.apiUrl}/permisos/`
    ).pipe(

      map(response => {

        return response.results ?? response;

      })

    );

  }


  getRolPermisos(idRol: number): Observable<{ permisos: number[] }> {

    return this.http.get<{ permisos: number[] }>(
      `${this.apiUrl}/roles/${idRol}/permisos/`
    );

  }


  actualizarRolPermisos(idRol: number, permisos: number[]): Observable<{ permisos: number[] }> {

    return this.http.put<{ permisos: number[] }>(
      `${this.apiUrl}/roles/${idRol}/permisos/`,
      { permisos }
    );

  }


  getBitacora(): Observable<any[]> {

    return this.http.get<any>(
      `${this.apiUrl}/bitacora/`
    ).pipe(

      map(response => {

        return response.results ?? response;

      })

    );

  }


  getClientes(): Observable<any[]> {

    return this.http.get<any>(
      `${this.apiUrl}/usuarios/?rol=CLIENTE`
    ).pipe(

      map(response => {

        return response.results ?? response;

      })

    );

  }

}