import { CommonModule } from '@angular/common';
import { Component, computed, inject, input } from '@angular/core';
import { UiHelperService } from '../../core';

@Component({
  selector: 'app-fair-price',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (value() != null) {
      <p [class]="valueClass()">R$ {{ value() | number: '1.2-2' }}</p>
      @if (basis()) {
        <p class="fi-caption text-ink-3 m-0">{{ basis() }}</p>
      }
    } @else {
      <p class="fi-caption text-indeterminate m-0">{{ absent() }}</p>
    }
  `,
})
export class FairPriceComponent {
  private readonly ui = inject(UiHelperService);

  readonly value = input<number | null>(null);

  /**
   * Quantos métodos formaram o número. Um preço justo de um método só não é consenso, e a tela
   * tem de dizer qual dos dois é — `/descobrir` mostrava Bazin cru enquanto `/ativo` dizia
   * "consenso de 3 métodos" para o mesmo ativo.
   */
  readonly methods = input<number | null>(null);

  /** Nome do método, quando a cifra é de um só (Bazin, Graham, P/VP justo). Vence `methods`. */
  readonly method = input<string>('');

  /**
   * A razão nomeada da ausência.
   *
   * Nunca um traço: "sem histórico de proventos" e "não se aplica a fundo imobiliário" são
   * respostas diferentes, e as duas são melhores que um campo vazio.
   */
  readonly absent = input<string>('sem preço justo');

  readonly size = input<'metric' | 'metric-sm'>('metric-sm');

  protected readonly valueClass = computed(() => `fi-${this.size()} text-ink m-0 fi-num` as const);

  protected readonly basis = computed(() => {
    const nome = this.method();
    if (nome) return `por ${nome}`;

    const n = this.methods();
    return n == null ? '' : this.ui.consensusLabel(n);
  });
}
