import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SuperadminService } from '../../../../core/services/superadmin.service';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { 
  heroShieldCheck, 
  heroFunnel, 
  heroArrowPath, 
  heroTrash, 
  heroChevronLeft, 
  heroChevronRight,
  heroUser,
  heroClock,
  heroBriefcase,
  heroCommandLine
} from '@ng-icons/heroicons/outline';

@Component({
  selector: 'app-bitacora',
  standalone: true,
  imports: [CommonModule, FormsModule, NgIconComponent],
  templateUrl: './bitacora.component.html',
  viewProviders: [provideIcons({ 
    heroShieldCheck, 
    heroFunnel, 
    heroArrowPath, 
    heroTrash, 
    heroChevronLeft, 
    heroChevronRight,
    heroUser,
    heroClock,
    heroBriefcase,
    heroCommandLine
  })]
})
export class BitacoraComponent implements OnInit {
  private superadminService = inject(SuperadminService);

  protected Math = Math;

  // State
  logs = signal<any[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);

  // Filters
  filterUser = signal('');
  filterDate = signal('');
  filterModule = signal('');
  filterAction = signal('');

  // Pagination
  currentPage = signal(1);
  pageSize = signal(15);

  // Computed
  filteredLogs = computed(() => {
    let list = this.logs();
    
    if (this.filterUser()) {
      const term = this.filterUser().toLowerCase();
      list = list.filter(l => 
        l.usuario_id?.toString().includes(term) || 
        l.descripcion?.toLowerCase().includes(term)
      );
    }

    if (this.filterDate()) {
      list = list.filter(l => l.fecha?.startsWith(this.filterDate()));
    }

    if (this.filterModule()) {
      list = list.filter(l => l.modulo?.toLowerCase() === this.filterModule().toLowerCase());
    }

    if (this.filterAction()) {
      list = list.filter(l => l.accion?.toLowerCase().includes(this.filterAction().toLowerCase()));
    }

    return list;
  });

  paginatedLogs = computed(() => {
    const start = (this.currentPage() - 1) * this.pageSize();
    return this.filteredLogs().slice(start, start + this.pageSize());
  });

  totalPages = computed(() => {
    return Math.ceil(this.filteredLogs().length / this.pageSize());
  });

  ngOnInit(): void {
    this.loadLogs();
  }

  loadLogs() {
    this.loading.set(true);
    this.superadminService.getBitacora().subscribe({
      next: (data) => {
        // Ordenar por fecha descendente
        this.logs.set(data.sort((a, b) => new Date(b.fecha).getTime() - new Date(a.fecha).getTime()));
        this.loading.set(false);
      },
      error: (err) => {
        console.error(err);
        this.error.set('Error al cargar la bitácora de auditoría.');
        this.loading.set(false);
      }
    });
  }

  clearFilters() {
    this.filterUser.set('');
    this.filterDate.set('');
    this.filterModule.set('');
    this.filterAction.set('');
    this.currentPage.set(1);
  }

  getModuleBadgeClass(modulo: string): string {
    const m = modulo?.toLowerCase() || '';
    if (m.includes('auth')) return 'bg-purple-100 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400';
    if (m.includes('usuario')) return 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400';
    if (m.includes('vehiculo')) return 'bg-orange-100 text-orange-700 dark:bg-orange-500/10 dark:text-orange-400';
    if (m.includes('incidente')) return 'bg-red-100 text-red-700 dark:bg-red-500/10 dark:text-red-400';
    return 'bg-slate-100 text-slate-700 dark:bg-slate-500/10 dark:text-slate-400';
  }

  getResultBadgeClass(accion: string): string {
    const a = accion?.toLowerCase() || '';
    if (a.includes('error') || a.includes('fallid')) return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400 border border-red-200 dark:border-red-500/30';
    return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30';
  }
}
