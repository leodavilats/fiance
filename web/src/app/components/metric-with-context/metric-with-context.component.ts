import { CommonModule } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { FiState, stateTextClass } from '../../core';

@Component({
  selector: 'app-metric-with-context',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="flex flex-col gap-0.5">
      <span class="fi-eyebrow text-ink-3">{{ label() }}</span>

      <span [class]="valueClass()">{{ known() ? value() : '—' }}</span>

      @if (known() && anchor()) {
        <span class="fi-caption text-ink-3">{{ anchor() }}</span>
      } @else if (!known()) {
        <span class="fi-caption text-indeterminate">{{ missingReason() || 'Sem dado' }}</span>
      }
    </div>
  `,
})
export class MetricWithContextComponent {
  readonly label = input.required<string>();

  readonly value = input<string | null>(null);

  readonly anchor = input<string>('');

  readonly missingReason = input<string>('');

  readonly state = input<FiState>('neutral');
  readonly size = input<'metric' | 'metric-sm'>('metric-sm');

  readonly known = computed(() => {
    const v = this.value();
    return v !== null && v !== '' && v !== '—';
  });

  valueClass(): string {
    if (!this.known()) return 'fi-metric-sm text-indeterminate';
    const tint = this.state() === 'neutral' ? 'text-ink' : stateTextClass(this.state());
    return `fi-${this.size()} ${tint}`;
  }
}
