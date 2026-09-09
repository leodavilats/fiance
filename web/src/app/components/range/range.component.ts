import { DecimalPipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';

/**
 * Um número projetado, que só existe como faixa.
 *
 * `analysis/scenarios.py` devolve `_low`/`_high` como campos obrigatórios, e o `lint:ui` recusa
 * tela que mostre `portfolio_value` ou `passive_income_monthly` sem eles — mas a faixa era
 * escrita à mão em cada projeção, e as duas plataformas divergiram: o web mostrava o cenário
 * base sob a faixa e o mobile não mostrava.
 *
 * É atributo, e não elemento, para o par nome/valor continuar sendo `<dt>`/`<dd>` dentro do
 * `<dl>`: um elemento no meio quebraria a lista de definição, que é o que o leitor de tela usa
 * para parear rótulo e cifra.
 */
@Component({
  selector: '[appRange]',
  standalone: true,
  imports: [DecimalPipe],
  template: `
    @if (label()) {
      <dt class="fi-eyebrow text-ink-3">{{ label() }}</dt>
    }

    <dd class="fi-metric-sm text-ink m-0 mt-1">
      entre R$ {{ low() | number: casas() }} e R$ {{ high() | number: casas() }}
    </dd>

    @if (base() !== null) {
      <dd class="fi-caption text-ink-3 m-0">cenário base: R$ {{ base() | number: casas() }}</dd>
    }

    @if (hypothesis()) {
      <dd class="fi-caption text-ink-3 m-0">{{ hypothesis() }}</dd>
    }
  `,
})
export class RangeComponent {
  readonly low = input.required<number>();
  readonly high = input.required<number>();

  /** O cenário central. Sai como legenda sob a faixa, nunca no lugar dela. */
  readonly base = input<number | null>(null);

  readonly label = input<string>('');

  /** A premissa que sustenta a faixa, quando ela não é óbvia pelo rótulo. */
  readonly hypothesis = input<string>('');

  /** Renda mensal se lê em centavos; patrimônio a cinco anos, não. */
  readonly cents = input(false);

  protected readonly casas = computed(() => (this.cents() ? '1.2-2' : '1.0-0'));
}
