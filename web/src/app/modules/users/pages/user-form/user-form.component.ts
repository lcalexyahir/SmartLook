import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UserService } from '../../../../core/services/user.service';
import { Router } from '@angular/router';


@Component({
  selector: 'app-user-form',
  templateUrl: './user-form.component.html',
  styleUrls: ['./user-form.component.scss']
})
export class UserFormComponent implements OnInit {


  form!: FormGroup;

  roles:any[] = [];


  constructor(
    private fb: FormBuilder,
    private userService: UserService,
    private router: Router
  ){}



  ngOnInit(): void {


    this.form = this.fb.group({

      nombres:[
        '',
        Validators.required
      ],

      apellidos:[
        '',
        Validators.required
      ],

      correo:[
        '',
        [
          Validators.required,
          Validators.email
        ]
      ],

      telefono:[
        ''
      ],

      password:[
        '',
        Validators.required
      ],

      rol:[
        '',
        Validators.required
      ]

    });



    this.cargarRoles();


  }




  cargarRoles(){

    this.userService.getRoles()
      .subscribe({

        next:(data)=>{

          this.roles=data;

        }

      });

  }





  guardar(){


    if(this.form.invalid){

      return;

    }



    const data = {


      nombres:this.form.value.nombres,

      apellidos:this.form.value.apellidos,

      correo:this.form.value.correo,

      telefono:this.form.value.telefono,

      password:this.form.value.password,

      rol:this.form.value.rol


    };



    this.userService.crearUsuario(data)
      .subscribe({

        next:(respuesta)=>{


          alert("Usuario creado correctamente");


          this.router.navigate([
            '/users'
          ]);


        },


        error:(error)=>{

          console.error(error);

          alert("Error creando usuario");

        }


      });


  }


}