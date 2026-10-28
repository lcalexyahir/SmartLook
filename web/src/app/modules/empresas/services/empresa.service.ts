// web/src/app/modules/empresas/services/empresa.service.ts
//
// NUEVO (SaaS): empresas (tenants) de la plataforma, su logo, su suscripción
// y sus sucursales. El SUPER_ADMIN ve y registra todas; el ADMIN_EMPRESA solo
// la suya (el backend responde 404 a lo ajeno).
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

export interface SuscripcionResumen {
  plan_codigo: string;
  plan_nombre: string;
  fecha_inicio: string;
  fecha_vencimiento: string;
  estado: string;
  vigente: boolean;
  dias_restantes: number;
}

export interface AdministradorEmpresa {
  id_usuario: number;
  nombre: string;
  correo: string;
  telefono: string | null;
}

export interface Empresa {
  id_empresa: number;
  uuid: string;
  nombre: string;
  slug: string;
  nit: string | null;
  correo_contacto: string | null;
  telefono: string | null;
  logo: string | null;
  estado: string;
  fecha_creacion: string;
  administrador: AdministradorEmpresa | null;
  suscripcion: SuscripcionResumen | null;
  total_sucursales: number;
}

@Injectable({
  providedIn: 'root'
})
export class EmpresaService {
  constructor(private api: ApiService) {}

  listar(): Observable<any> {
    return this.api.get('/auth/empresas/', { page_size: 100 });
  }

  obtener(id: number): Observable<Empresa> {
    return this.api.get<Empresa>(`/auth/empresas/${id}/`);
  }

  crear(datos: any): Observable<Empresa> {
    return this.api.post<Empresa>('/auth/empresas/', datos);
  }

  actualizar(id: number, datos: any): Observable<Empresa> {
    return this.api.patch<Empresa>(`/auth/empresas/${id}/`, datos);
  }

  cambiarEstado(id: number, estado: 'ACTIVA' | 'SUSPENDIDA'): Observable<Empresa> {
    return this.api.post<Empresa>(`/auth/empresas/${id}/cambiar-estado/`, { estado });
  }

  planes(): Observable<any> {
    return this.api.get('/auth/planes/');
  }

  ciudades(): Observable<any> {
    return this.api.get('/catalog/ciudades/', { page_size: 100 });
  }

  // El SUPER_ADMIN filtra por empresa con ?empresa=<slug>; el personal ya
  // recibe solo las de su empresa.
  sucursales(slug: string): Observable<any> {
    return this.api.get('/catalog/sucursales/', { empresa: slug, page_size: 100 });
  }

  // El SUPER_ADMIN indica la empresa con id_empresa; al personal se le asigna la suya.
  crearSucursal(datos: any): Observable<any> {
    return this.api.post('/catalog/sucursales/', datos);
  }
}

// Convierte la respuesta de error del backend (detail, error o errores por
// campo, incluso anidados) en un solo texto para mostrar al usuario.
export function mensajeDeError(err: any, porDefecto: string): string {
  const cuerpo = err?.error;
  if (!cuerpo || typeof cuerpo !== 'object') {
    return porDefecto;
  }
  if (cuerpo.detail) {
    return String(cuerpo.detail);
  }
  if (cuerpo.error) {
    return String(cuerpo.error);
  }
  const partes: string[] = [];
  const recorrer = (valor: any): void => {
    if (Array.isArray(valor)) {
      valor.forEach(recorrer);
    } else if (valor && typeof valor === 'object') {
      Object.values(valor).forEach(recorrer);
    } else if (valor) {
      partes.push(String(valor));
    }
  };
  recorrer(cuerpo);
  return partes.length > 0 ? partes.join(' ') : porDefecto;
}

// "2026-10-27" -> "27/10/2026" (sin pasar por Date para no correr el día por la zona horaria).
export function formatoFecha(fecha: string | null | undefined): string {
  if (!fecha) {
    return '';
  }
  const [anio, mes, dia] = fecha.slice(0, 10).split('-');
  return `${dia}/${mes}/${anio}`;
}

// Iniciales para el avatar cuando la empresa no tiene logo (ej. "LOOK FASHION" -> "LF").
export function iniciales(nombre: string | null | undefined): string {
  return (nombre || '')
    .split(/\s+/)
    .filter(p => p.length > 0)
    .slice(0, 2)
    .map(p => p[0].toUpperCase())
    .join('');
}