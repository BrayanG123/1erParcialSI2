import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormControl } from '@angular/forms';

@Component({
  selector: 'app-auth-input',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="space-y-2">
      <label *ngIf="label" class="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">{{ label }}</label>
      <div class="relative flex items-center">
        <input 
          [formControl]="control" 
          [type]="type"
          [class]="inputClasses"
          [placeholder]="placeholder">
        <span *ngIf="icon" class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400">
          <ng-container *ngTemplateOutlet="iconTemplate"></ng-container>
        </span>
      </div>
    </div>

    <ng-template #iconTemplate>
      <div [innerHTML]="icon" class="w-5 h-5"></div>
    </ng-template>
  `
})
export class AuthInputComponent {
  @Input() label: string = '';
  @Input() placeholder: string = '';
  @Input() type: string = 'text';
  @Input() control!: FormControl;
  @Input() icon?: string;

  get inputClasses() {
    return 'w-full pl-5 pr-12 py-4 rounded-xl border border-slate-200 bg-white text-[#1C2434] focus:border-indigo-500 focus:ring-4 focus:ring-indigo-50 outline-none transition-all placeholder:text-slate-300 font-medium text-sm';
  }
}
