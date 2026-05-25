import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../../core/auth/services/auth.service';
import { AuthInputComponent } from '../../../../shared/components/form/input/auth-input.component';
import { PrimaryButtonComponent } from '../../../../shared/components/ui/button/primary-button.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, AuthInputComponent, PrimaryButtonComponent],
  templateUrl: './login.component.html'
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  loginError = '';
  isSubmitting = false;

  loginForm = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(3)]]
  });

  onSubmit() {
    this.loginError = '';
    if (this.loginForm.valid) {
      this.isSubmitting = true;
      this.authService.login(this.loginForm.getRawValue()).subscribe({
        next: () => {
          // El AuthService ya se encarga de la redirección
          this.isSubmitting = false;
        },
        error: () => {
          this.isSubmitting = false;
          this.loginError = 'Credenciales incorrectas';
        }
      });
    }
  }
}
