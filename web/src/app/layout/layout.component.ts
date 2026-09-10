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


  constructor(

    private authService: AuthService,

    private router: Router

  ) {


    const data = localStorage.getItem('usuario');


    if (data) {

      this.usuario = JSON.parse(data);

    }


  }



  cerrarSesion(): void {


    this.authService.logout();


  }



}