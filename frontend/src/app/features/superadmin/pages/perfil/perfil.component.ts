import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { UserService } from '../../../usuarios/services/user.service';
import { Usuario } from '../../../usuarios/models/usuario.model';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { heroUserCircle, heroCamera, heroEnvelope, heroPhone, heroIdentification } from '@ng-icons/heroicons/outline';

@Component({
  selector: 'app-superadmin-perfil',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, NgIconComponent],
  templateUrl: './perfil.component.html',
  viewProviders: [provideIcons({ heroUserCircle, heroCamera, heroEnvelope, heroPhone, heroIdentification })]
})
export class SuperadminPerfilComponent implements OnInit {
  private userService = inject(UserService);
  private fb = inject(FormBuilder);

  usuario = signal<Usuario | null>(null);
  loading = signal(true);
  submitting = signal(false);

  perfilForm: FormGroup = this.fb.group({
    nombre: ['', [Validators.required]],
    apellido: ['', [Validators.required]],
    telefono: [''],
    profile_image_url: ['']
  });

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile() {
    this.loading.set(true);
    this.userService.getMe().subscribe({
      next: (user: any) => {
        this.usuario.set(user);
        this.perfilForm.patchValue({
          nombre: user.nombre,
          apellido: user.apellido,
        });
        this.loading.set(false);
      },
      error: (err: any) => {
        console.error('Error al cargar perfil', err);
        this.loading.set(false);
      }
    });
  }

  onSubmit() {
    if (this.perfilForm.invalid) return;

    this.submitting.set(true);
    this.userService.updateMe(this.perfilForm.value).subscribe({
      next: (updatedUser: any) => {
        this.usuario.set(updatedUser);
        this.submitting.set(false);
        alert('Perfil actualizado correctamente');
      },
      error: (err: any) => {
        console.error('Error al actualizar perfil', err);
        this.submitting.set(false);
        alert('Ocurri un error al actualizar los datos');
      }
    });
  }
}
