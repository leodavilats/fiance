import { CommonModule } from '@angular/common';
import { Component, input, output } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { FiState } from '../../core';

@Component({
  selector: 'app-insight',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div
      class="flex items-start gap-3 py-3"
      [class.border-t]="divided()"
      [class.border-hairline]="divided()"
    >
      <lucide-icon
        [name]="icon()"
        size="16"
        class="mt-0.5 shrink-0"
        [class]="stateClass()"
        aria-hidden="true"
      ></lucide-icon>

      <div class="flex-1 min-w-0">
        <!-- O que aconteceu -->
        <div class="fi-verdict-sm text-ink">{{ title() }}</div>

        <!-- Por que importa -->
        @if (detail()) {
          <div class="fi-body text-ink-2 mt-0.5">{{ detail() }}</div>
        }

        <!-- O que sustenta a leitura -->
        @if (evidence()) {
          <div class="fi-caption text-ink-3 mt-1">{{ evidence() }}</div>
        }
      </div>

      <!-- O que posso fazer -->
      @if (actionLabel()) {
        <button
          type="button"
          class="shrink-0 px-3 py-1.5 rounded-md border border-hairline fi-caption text-ink hover:bg-ground-2 transition-colors cursor-pointer bg-transparent"
          (click)="action.emit()"
        >
          {{ actionLabel() }}
        </button>
      }
    </div>
  `,
})
export class InsightComponent {
  readonly title = input.required<string>();
  readonly detail = input<string>('');
  readonly evidence = input<string>('');
  readonly actionLabel = input<string>('');
  readonly state = input<FiState>('neutral');
  readonly divided = input(false);

  readonly action = output<void>();

  icon(): string {
    switch (this.state()) {
      case 'favorable':
        return 'circle-check';
      case 'attention':
        return 'triangle-alert';
      case 'adverse':
        return 'circle-alert';
      case 'indeterminate':
        return 'circle-help';
      default:
        return 'circle-dot';
    }
  }

  stateClass(): string {
    switch (this.state()) {
      case 'favorable':
        return 'text-favorable';
      case 'attention':
        return 'text-attention';
      case 'adverse':
        return 'text-adverse';
      case 'indeterminate':
        return 'text-indeterminate';
      default:
        return 'text-ink-3';
    }
  }
}
