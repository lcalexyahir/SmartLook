// web/src/app/modules/auth/pages/login/login.component.ts
//
// Único cambio respecto al original: el redirect tras login ya no es
// fijo a '/dashboard'. Ahora depende del rol del usuario autenticado.

import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  loginForm!: FormGroup;
  loading = false;
  errorMessage: string | null = null;
  mostrarPassword = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loginForm = this.fb.group({
      correo: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]]
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) return;

    this.loading = true;
    this.errorMessage = null;

    const { correo, password } = this.loginForm.value;

    this.authService.login(correo, password).subscribe({
      next: () => {
        this.loading = false;

        // El cliente tiene su propia vista (catálogo con reservas);
        // cualquier otro rol va al panel administrativo.
        if (this.authService.esCliente()) {
          this.router.navigate(['/catalog']);
        } else {
          this.router.navigate(['/dashboard']);
        }
      },
      error: (error) => {
        this.loading = false;
        this.errorMessage = error.error?.error || 'Error al iniciar sesión. Verifique sus credenciales.';
      }
    });
  }

  get correoControl() { return this.loginForm.get('correo'); }
  get passwordControl() { return this.loginForm.get('password'); }
}