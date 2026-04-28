import { Component, ElementRef, ViewChild, OnDestroy, AfterViewInit, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SidebarService } from '../../../../../services/sidebar.service';
import { UserDropdownComponent } from '../../../../../components/header/user-dropdown/user-dropdown.component';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    UserDropdownComponent,
  ],
  templateUrl: './app-header.component.html',
})
export class AppHeaderComponent {
  // Recibimos los datos de Eva desde el AdminLayout
  @Input() userName: string = 'Usuario';
  @Input() userRole: string = 'Admin';

  isApplicationMenuOpen = false;
  readonly isMobileOpen$;

  constructor(public sidebarService: SidebarService) {
    this.isMobileOpen$ = this.sidebarService.isMobileOpen$;
  }

  handleToggle() {
    if (window.innerWidth >= 1280) {
      this.sidebarService.toggleExpanded();
    } else {
      this.sidebarService.toggleMobileOpen();
    }
  }

  toggleApplicationMenu() {
    this.isApplicationMenuOpen = !this.isApplicationMenuOpen;
  }
}
