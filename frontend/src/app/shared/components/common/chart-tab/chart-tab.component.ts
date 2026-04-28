import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-chart-tab',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="flex items-center gap-2 p-1 bg-gray-100 rounded-lg dark:bg-gray-800">
      @for (tab of tabs; track tab) {
        <button
          (click)="onTabChange(tab)"
          [class]="tab === activeTab ? 'bg-white shadow-sm text-gray-800 dark:bg-gray-700 dark:text-white' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'"
          class="px-3 py-1.5 text-xs font-medium rounded-md transition-all"
        >
          {{ tab }}
        </button>
      }
    </div>
  `
})
export class ChartTabComponent {
  @Input() tabs: string[] = ['Day', 'Week', 'Month'];
  @Input() activeTab: string = 'Month';
  @Output() tabChange = new EventEmitter<string>();

  onTabChange(tab: string) {
    this.activeTab = tab;
    this.tabChange.emit(tab);
  }
}
