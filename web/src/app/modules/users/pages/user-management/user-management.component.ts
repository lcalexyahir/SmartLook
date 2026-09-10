import { Component, OnInit } from '@angular/core';

import { UserService } from '../../../../core/services/user.service';



@Component({
  selector: 'app-user-management',
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.scss']
})
export class UserManagementComponent implements OnInit {


  usuarios: any[] = [];


  constructor(
    private userService: UserService
  ){}



  ngOnInit(): void {

    this.cargarUsuarios();

  }



  cargarUsuarios(): void {

    this.userService.getUsuarios()
      .subscribe({

        next: (data) => {

          this.usuarios = data;

        },

        error: (err) => {

          console.error(
            'Error cargando usuarios',
            err
          );

        }

      });

  }


}