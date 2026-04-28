import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-checkbox',
  standalone: true,
  imports: [CommonModule],
  template: `
    <input 
      type="checkbox" 
      [checked]="checked" 
      (change)="onCheckedChange($event)"
      class="w-4 h-4 text-brand-500 border-gray-300 rounded focus:ring-brand-500"
    >
  `
})
export class CheckboxComponent {
  @Input() checked = false;
  @Output() checkedChange = new EventEmitter<boolean>();

  onCheckedChange(event: any) {
    this.checkedChange.emit(event.target.checked);
  }
}
