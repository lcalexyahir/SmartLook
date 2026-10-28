// web/src/app/core/auth/auth.service.ts
//
// MODIFICADO (SaaS - A.2): lee del JWT la empresa (tenant) del usuario
// (claims "empresa", "empresa_nombre", "id_empresa" e "id_sucursal") para
// mostrarla en el panel. El backend vuelve a validar esos datos en cada
// petición; aquí solo se usan para mostrarlos.
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, tap } from 'rxjs';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';
export interface EmpresaSesion {
  id: number | null;
  slug: string | null;
  nombre: string;
}
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
    private apiUrl = `${environment.apiUrl}/auth`;
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
      '/auth/login'
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
  /**
   * Devuelve los nombres de los roles del usuario logueado
   * (ej: ['CLIENTE'], ['ADMIN_EMPRESA']), leyendo lo que el
   * login guardó en localStorage. Si no hay sesión, devuelve [].
   */
  obtenerRoles(): string[] {
    const usuarioGuardado = localStorage.getItem('usuario');
    if (!usuarioGuardado) {
      return [];
    }
    try {
      const usuario = JSON.parse(usuarioGuardado);
      const roles = usuario?.roles ?? [];
      return roles.map((rol: any) => rol.nombre);
    } catch {
      return [];
    }
  }
  /**
   * true si el usuario logueado tiene el rol CLIENTE (y solo ese,
   * o entre otros). Usado para decidir a dónde redirigir tras login
   * y para bloquear el acceso a vistas administrativas.
   */
  esCliente(): boolean {
    return this.obtenerRoles().includes('CLIENTE');
  }
  /**
   * Datos (claims) del token de acceso, o null si no hay sesión o el token
   * no se puede leer. El token no se verifica aquí: eso lo hace el backend.
   */
  obtenerDatosToken(): any | null {
    const token = this.getToken();
    if (!token) {
      return null;
    }
    try {
      const partes = token.split('.');
      if (partes.length !== 3) {
        return null;
      }
      const base64 = partes[1].replace(/-/g, '+').replace(/_/g, '/');
      const relleno = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
      // atob devuelve bytes; se pasan a UTF-8 para respetar tildes y la ñ.
      const json = decodeURIComponent(
        atob(relleno)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(json);
    } catch {
      return null;
    }
  }
  /**
   * Empresa (tenant) del usuario según el JWT. Es null para SUPER_ADMIN y
   * clientes, que no pertenecen a ninguna empresa.
   */
  obtenerEmpresa(): EmpresaSesion | null {
    const datos = this.obtenerDatosToken();
    if (!datos?.empresa_nombre) {
      return null;
    }
    return {
      id: datos.id_empresa ?? null,
      slug: datos.empresa ?? null,
      nombre: datos.empresa_nombre
    };
  }
}