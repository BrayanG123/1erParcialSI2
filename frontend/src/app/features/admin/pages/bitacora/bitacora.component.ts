import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { AdminOpsService } from '../../../../core/services/admin-ops.service';
import { Bitacora_Evento } from '../../../../core/models/admin-ops.model';

@Component({
  selector: 'app-bitacora',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './bitacora.component.html'
})
export class BitacoraComponent implements OnInit {
  private adminOpsService = inject(AdminOpsService);

  eventos: Bitacora_Evento[] = [];
  usuarios_map: Record<number, string> = {};
  loading = false;
  error: string | null = null;

  ngOnInit(): void {
    this.cargarBitacora();
    this.cargarUsuarios();
  }

  cargarBitacora(): void {
    this.loading = true;
    this.error = null;
    this.adminOpsService.getBitacoraAdmin().subscribe({
      next: (data) => {
        this.eventos = Array.isArray(data) ? data : [];
        this.loading = false;
      },
      error: () => {
        this.eventos = [];
        this.error = 'No se pudo cargar la bitácora.';
        this.loading = false;
      }
    });
  }

  cargarUsuarios(): void {
    this.adminOpsService.getUsuariosAdmin().subscribe({
      next: (data) => {
        const usuarios = Array.isArray(data) ? data : [];
        const mapa: Record<number, string> = {};
        usuarios.forEach((usuario) => {
          mapa[usuario.id] = `${usuario.nombre || ''} ${usuario.apellido || ''}`.trim() || `Usuario #${usuario.id}`;
        });
        this.usuarios_map = mapa;
      },
      error: () => {
        this.usuarios_map = {};
      }
    });
  }

  getUsuarioNombre(evento: Bitacora_Evento): string {
    const usuario_id = Number(evento.usuario_id || 0);
    if (!usuario_id) return 'Sistema';
    return this.usuarios_map[usuario_id] || `Usuario #${usuario_id}`;
  }
}
