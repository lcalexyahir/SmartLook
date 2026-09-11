// web/src/app/layout/layout.component.ts
//
// Único cambio: se agrega la propiedad esCliente, calculada con
// authService.esCliente(), para que la plantilla oculte las opciones
// administrativas cuando corresponda.

import { Component } from '@angular/core';

import { Router } from '@angular/router';

import { AuthService } from '../core/auth/auth.service';


@Component({

  selector: 'app-layout',

  templateUrl: './layout.component.html',

  styleUrls: ['./layout.component.css']

})
export class LayoutComponent {

  usuario: any = null;
  esCliente = false;

  constructor(

    private authService: AuthService,

    private router: Router

  ) {

    const data = localStorage.getItem('usuario');

    if (data) {

      this.usuario = JSON.parse(data);

    }

    this.esCliente = this.authService.esCliente();

  }


  cerrarSesion(): void {

    this.authService.logout();

  }


}