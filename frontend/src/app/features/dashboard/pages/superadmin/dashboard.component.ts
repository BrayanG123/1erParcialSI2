import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { SuperadminService } from '../../../../core/services/superadmin.service';
import { SuperadminKpis } from '../../../../core/models/superadmin.model';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { 
  heroUsers, 
  heroHomeModern, 
  heroShieldCheck, 
  heroUserGroup, 
  heroArrowTrendingUp 
} from '@ng-icons/heroicons/outline';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, NgIconComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
  viewProviders: [provideIcons({ 
    heroUsers, 
    heroHomeModern, 
    heroShieldCheck, 
    heroUserGroup, 
    heroArrowTrendingUp 
  })]
})
export class DashboardComponent implements OnInit {
  private superadminService = inject(SuperadminService);

  kpis: SuperadminKpis | null = null;
  loading = true;
  error: string | null = null;

  ngOnInit(): void {
    this.superadminService.getKpis().subscribe({
      next: (data: any) => {
        this.kpis = data;
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar los KPIs.';
        this.loading = false;
      }
    });
  }
}
