import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-avatar-text',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="flex items-center justify-center w-10 h-10 rounded-full bg-brand-100 text-brand-600 font-medium">
      {{ initials || getNameInitials() }}
    </div>
  `
})
export class AvatarTextComponent {
  @Input() name: string = '';
  @Input() initials?: string;

  getNameInitials() {
    if (!this.name) return '';
    return this.name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .substring(0, 2);
  }
}
