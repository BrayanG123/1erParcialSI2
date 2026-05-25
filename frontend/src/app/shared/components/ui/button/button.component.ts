import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-button',
  standalone: true,
  imports: [CommonModule],
  template: `
    <button 
      [class]="variantClasses" 
      [disabled]="disabled"
      (click)="btnClick.emit($event)"
    >
      <slot></slot>
      <ng-content></ng-content>
    </button>
  `
})
export class ButtonComponent {
  @Input() variant: 'primary' | 'secondary' | 'outline' = 'primary';
  @Input() size: 'sm' | 'md' | 'lg' = 'md';
  @Input() disabled = false;
  @Output() btnClick = new EventEmitter<any>();

  get variantClasses() {
    const base = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors';
    const sizes = {
      sm: 'px-3 py-1.5 text-xs',
      md: 'px-4 py-2 text-sm',
      lg: 'px-5 py-2.5 text-base'
    };
    const variants = {
      primary: 'bg-brand-500 text-white hover:bg-brand-600',
      secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
      outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50'
    };
    return `${base} ${sizes[this.size]} ${variants[this.variant]}`;
  }
}
