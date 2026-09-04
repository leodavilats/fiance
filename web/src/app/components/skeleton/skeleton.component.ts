import { CommonModule } from '@angular/common';
import { Component, computed, input } from '@angular/core';

export type SkeletonShape =
  'money-xl' | 'verdict' | 'metric' | 'title' | 'body' | 'caption' | 'ruler' | 'row';

@Component({
  selector: 'app-skeleton',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div [attr.aria-hidden]="true" class="flex flex-col" [style.gap.px]="gap()">
      @for (line of lines(); track $index) {
        <div
          class="fi-skeleton rounded-sm"
          [style.height.px]="height()"
          [style.width]="line"
          [style.margin-top.px]="shape() === 'row' && $index > 0 ? rowGap() : 0"
        ></div>
      }
    </div>
  `,
  styles: [
    `
      .fi-skeleton {
        background: color-mix(in srgb, var(--fi-ink-3) 16%, transparent);
        animation: fi-skeleton-pulse 1.4s ease-in-out infinite;
      }
      @keyframes fi-skeleton-pulse {
        0%,
        100% {
          opacity: 1;
        }
        50% {
          opacity: 0.55;
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .fi-skeleton {
          animation: none;
        }
      }
    `,
  ],
})
export class SkeletonComponent {
  readonly shape = input<SkeletonShape>('body');

  readonly count = input(1);

  readonly height = computed(() => {
    switch (this.shape()) {
      case 'money-xl':
        return 48;
      case 'verdict':
        return 28;
      case 'metric':
        return 28;
      case 'title':
        return 20;
      case 'ruler':
        return 8;
      case 'row':
        return 16;
      case 'caption':
        return 12;
      default:
        return 14;
    }
  });

  readonly gap = computed(() => (this.shape() === 'row' ? 0 : 8));
  readonly rowGap = computed(() => 20);

  readonly lines = computed(() => {
    const widths: Record<SkeletonShape, string[]> = {
      'money-xl': ['58%'],
      verdict: ['82%', '64%'],
      metric: ['40%'],
      title: ['46%'],
      body: ['100%', '88%', '72%'],
      caption: ['38%'],
      ruler: ['100%'],
      row: ['100%'],
    };
    const base = widths[this.shape()];
    const n = this.count();
    if (this.shape() === 'row') return Array.from({ length: n }, () => '100%');
    if (n <= 1) return base.slice(0, this.shape() === 'body' ? base.length : 1);
    return Array.from({ length: n }, (_, i) => base[i % base.length]);
  });
}
