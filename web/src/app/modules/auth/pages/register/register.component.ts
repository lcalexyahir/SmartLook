import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent implements OnInit {
  registerForm!: FormGroup;
  loading = false;
  successMessage: string | null = null;
  errorMessage: string | null = null;
  mostrarPassword = false;
  mostrarPasswordConfirm = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.registerForm = this.fb.group({
      nombres: ['', [Validators.required, Validators.minLength(2)]],
      apellidos: ['', [Validators.required, Validators.minLength(2)]],
      correo: ['', [Validators.required, Validators.email]],
      // Alineado con el backend (RN7): 8 dígitos, inicia en 6 o 7,
      // con prefijo +591 opcional. Campo opcional.
      telefono: ['', [Validators.pattern('^(\\+591)?[67][0-9]{7}$')]],
      // Alineado con el backend (RN2): mínimo 8 caracteres.
      password: ['', [Validators.required, Validators.minLength(8)]],
      password_confirm: ['', [Validators.required]],
      direccion: [''],
      fecha_nacimiento: ['']
    });
  }

  onSubmit(): void {
    if (this.registerForm.invalid) return;

    this.loading = true;
    this.errorMessage = null;
    this.successMessage = null;

    const formData = this.registerForm.value;

    if (formData.password !== formData.password_confirm) {
      this.errorMessage = 'Las contraseñas no coinciden.';
      this.loading = false;
      return;
    }

    this.authService.register(formData).subscribe({
      next: (response) => {
        this.loading = false;
        this.successMessage = 'Registro exitoso. Redirigiendo al login...';
        setTimeout(() => {
          this.router.navigate(['/auth/login']);
        }, 2000);
      },
      error: (error) => {
        this.loading = false;
        this.errorMessage = error.error?.error
          || error.error?.correo?.[0]
          || error.error?.password?.[0]
          || error.error?.password_confirm?.[0]
          || error.error?.telefono?.[0]
          || error.error?.fecha_nacimiento?.[0]
          || 'Error al registrar. Verifique los datos.';
      }
    });
  }
}