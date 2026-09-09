import { Component, computed, input } from '@angular/core';
import { dadoEnvelhecido, idadeDoDado } from '../../core/data-age';

@Component({
  selector: 'app-data-age',
  standalone: true,
  template: `
    @if (frase(); as quando) {
      <span
        class="fi-caption"
        [class.text-ink-3]="!envelhecido()"
        [class.text-attention]="envelhecido()"
        [attr.title]="titulo()"
      >
        {{ label() }} {{ quando }}
      </span>
    } @else if (semCarimbo()) {
      <span class="fi-caption text-ink-3" title="A fonte não informou quando este dado foi lido">
        {{ label() }} sem data de leitura
      </span>
    }
  `,
})
export class DataAgeComponent {
  /** `as_of` do coletor, em segundos epoch. */
  readonly asOf = input<number | null | undefined>(null);

  readonly label = input<string>('Cotação de');

  /** Sem carimbo a tela cala por padrão; ligue onde a ausência de data é o próprio recado. */
  readonly semCarimbo = input(false);

  protected readonly frase = computed(() => idadeDoDado(this.asOf()));
  protected readonly envelhecido = computed(() => dadoEnvelhecido(this.asOf()));
  protected readonly titulo = computed(() =>
    this.envelhecido()
      ? 'Esta leitura não é de hoje — a fonte pode estar indisponível'
      : 'Momento em que a fonte foi lida'
  );
}
