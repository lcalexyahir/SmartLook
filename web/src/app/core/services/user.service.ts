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


}