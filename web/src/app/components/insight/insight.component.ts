import { CommonModule } from '@angular/common';
import { Component, computed, input, output } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { FiState } from '../../core';

export type InsightLevel = 'essencial' | 'completo' | 'avancado';

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
        <div class="fi-verdict-sm text-ink">{{ title() }}</div>

        @if (mostraDetalhe() && detail()) {
          <div class="fi-body text-ink-2 mt-0.5">{{ detail() }}</div>
        }

        @if (mostraEvidencia() && evidence()) {
          <div class="fi-caption text-ink-3 mt-1">{{ evidence() }}</div>
        }
      </div>

      @if (actionLabel()) {
        <button type="button" class="btn-secondary compact-btn shrink-0" (click)="action.emit()">
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
  readonly level = input<InsightLevel>('completo');

  readonly action = output<void>();

  readonly mostraDetalhe = computed(() => this.level() !== 'essencial');
  readonly mostraEvidencia = computed(() => this.level() === 'avancado');

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
