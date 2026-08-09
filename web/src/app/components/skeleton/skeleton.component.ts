import { Component, computed, input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-skeleton',
  standalone: true,
  imports: [CommonModule],
  template: `
    @for (i of rowsArray(); track i) {
      <div class="skeleton mb-2" [style.height]="height()" [style.width]="width()"></div>
    }
  `,
})
export class SkeletonComponent {
  rows = input<number>(1);
  height = input<string>('20px');
  width = input<string>('100%');
  rowsArray = computed(() => Array.from({ length: this.rows() }, (_, i) => i));
}
