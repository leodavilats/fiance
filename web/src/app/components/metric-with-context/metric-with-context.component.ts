import { CommonModule } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { FiState, stateTextClass } from '../../core';

/**
 * Um número com a âncora que o torna interpretável — **e nada quando a âncora
 * não existe**.
 *
 * "ROE de 14%" não diz nada sozinho; "14%, contra 15% que é o piso confortável"
 * decide. Mas se o produto não tem a referência, o componente mostra o valor e
 * cala sobre o resto: âncora inventada é pior que âncora ausente (§57).
 */
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
  /** Já formatado por quem chama — o componente não escolhe casas nem moeda. */
  readonly value = input<string | null>(null);
  /** A referência que dá sentido: meta, CDI, setor, histórico. Opcional. */
  readonly anchor = input<string>('');
  /** Por que o dado não existe, quando não existe. */
  readonly missingReason = input<string>('');
  /** Julgamento sobre o valor, quando o backend tem um. Nunca calculado aqui. */
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
