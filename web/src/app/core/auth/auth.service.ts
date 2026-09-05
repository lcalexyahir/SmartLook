import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, tap } from 'rxjs';
import { Router } from '@angular/router';


export interface LoginResponse {

  tokens: {
    access: string;
    refresh: string;
  };

  usuario: any;

}



@Injectable({
  providedIn: 'root'
})
export class AuthService {


  private apiUrl = 'http://127.0.0.1:8000/api/auth';


  private usuarioSubject =
    new BehaviorSubject<any>(null);


  usuario$ =
    this.usuarioSubject.asObservable();



  constructor(
    private http: HttpClient,
    private router: Router
  ) {}



  login(
    correo: string,
    password: string
  ): Observable<LoginResponse> {


    return this.http.post<LoginResponse>(
      `${this.apiUrl}/login/`,
      {
        correo,
        password
      }

    ).pipe(

      tap(response => {


        localStorage.setItem(
          'access_token',
          response.tokens.access
        );


        localStorage.setItem(
          'refresh_token',
          response.tokens.refresh
        );


        localStorage.setItem(
          'usuario',
          JSON.stringify(response.usuario)
        );


        this.usuarioSubject.next(
          response.usuario
        );


      })

    );

  }




  register(
    data: any
  ): Observable<any> {


    return this.http.post(
      `${this.apiUrl}/registro/`,
      data
    );

  }





  logout(): void {


    localStorage.removeItem(
      'access_token'
    );


    localStorage.removeItem(
      'refresh_token'
    );


    localStorage.removeItem(
      'usuario'
    );


    this.router.navigate([
      '/login'
    ]);

  }





  getToken(): string | null {

    return localStorage.getItem(
      'access_token'
    );

  }




  estaAutenticado(): boolean {

    return !!this.getToken();

  }


}