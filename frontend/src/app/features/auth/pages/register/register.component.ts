import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router, RouterLink } from '@angular/router';
import { environment } from '../../../../../environments/environment.development';
import { AuthInputComponent } from '../../../../shared/components/form/input/auth-input.component';
import { PrimaryButtonComponent } from '../../../../shared/components/ui/button/primary-button.component';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, AuthInputComponent, PrimaryButtonComponent],
  templateUrl: './register.component.html'
})
export class RegisterComponent {
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private router = inject(Router);

  registerForm = this.fb.group({
    nombre: ['', [Validators.required, Validators.minLength(2)]],
    apellido: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]]
  });

  onSubmit() {
    if (this.registerForm.valid) {
      // Auto-generamos el username a partir del email (parte antes del @)
      // Reemplazamos cualquier carácter no alfanumérico por guión bajo
      const formValue = this.registerForm.value;
      const emailPrefix = formValue.email?.split('@')[0] || 'user';
      const generatedUsername = emailPrefix.toLowerCase().replace(/[^a-z0-9]/g, '_');

      const datosRegistro = {
        ...formValue,
        username: generatedUsername,
        rol: 'administrador'
      };

      this.http.post(`${environment.apiUrl}/auth/registro`, datosRegistro)
        .subscribe({
          next: () => {
            alert('¡Registro exitoso! Ya puedes iniciar sesión.');
            this.router.navigate(['/login']);
          },
          error: (err) => {
            console.error('Error en registro:', err);
            const mensajeError = err.error?.detail || 'Error al conectar con el servidor';
            alert('Error: ' + (typeof mensajeError === 'string' ? mensajeError : 'Datos inválidos o email ya registrado'));
          }
        });
    }
  }
}
