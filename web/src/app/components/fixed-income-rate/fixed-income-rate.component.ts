import { CommonModule } from '@angular/common';
import { Component, computed, input } from '@angular/core';

/**
 * "Rende quanto, **comparado a quê**?"
 *
 * 13,8% ao ano não significa nada sozinho: depende do CDI do dia, do imposto e
 * do prazo. A leitura primária é sempre a comparação — "~112% do CDI" —, e a
 * taxa contratada, o indexador, a liquidez e o IR ficam em disclosure (§16).
 *
 * Todos os números chegam prontos de `analysis/renda_fixa_analysis.py`: aqui não
 * se converte taxa, não se calcula imposto e não se estima equivalência.
 */
@Component({
  selector: 'app-fixed-income-rate',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="flex flex-col gap-1" [attr.aria-label]="ariaLabel()" role="group">
      <span class="fi-eyebrow text-ink-3">{{ label() }}</span>
      <span class="fi-metric text-ink">{{ headline() }}</span>
      <span class="fi-caption text-ink-3">{{ subline() }}</span>

      @if (showDetail()) {
        <dl class="grid grid-cols-2 gap-x-4 gap-y-1 m-0 mt-2">
          <dt class="fi-caption text-ink-3">Taxa contratada</dt>
          <dd class="fi-caption text-ink m-0 text-right fi-num">{{ contractedLabel() }}</dd>

          <dt class="fi-caption text-ink-3">Prazo</dt>
          <dd class="fi-caption text-ink m-0 text-right">
            <span class="fi-num">{{ prazoMeses() }}</span> meses
          </dd>

          <dt class="fi-caption text-ink-3">Liquidez</dt>
          <dd class="fi-caption text-ink m-0 text-right">{{ liquidezLabel() }}</dd>

          <dt class="fi-caption text-ink-3">Imposto de renda</dt>
          <dd class="fi-caption text-ink m-0 text-right">{{ irLabel() }}</dd>
        </dl>
      }
    </div>
  `,
})
export class FixedIncomeRateComponent {
  readonly label = input('Rendimento');
  /** Taxa anual efetiva líquida, em % — do backend. */
  readonly netRatePct = input<number | null>(null);
  /** Equivalência ao CDI já calculada pelo backend, em %. */
  readonly pctOfCdi = input<number | null>(null);
  /** Indexador contratado: 'pre_fixado' | 'pos_fixado' | 'hibrido'. */
  readonly rateKind = input<string>('');
  /** Taxa contratada em % (ou % do CDI, quando pós-fixado). */
  readonly contractedRate = input<number | null>(null);
  readonly prazoMeses = input<number>(0);
  readonly liquidez = input<string>('');
  readonly isentoIr = input(false);
  readonly irAliquotaPct = input<number | null>(null);
  readonly showDetail = input(true);

  /** A âncora vem antes do número absoluto — e some quando não existe. */
  readonly headline = computed(() => {
    const cdi = this.pctOfCdi();
    if (cdi !== null) return `~${cdi.toFixed(0)}% do CDI`;
    const net = this.netRatePct();
    return net !== null ? `${net.toFixed(2)}% a.a.` : '—';
  });

  readonly subline = computed(() => {
    const net = this.netRatePct();
    if (net === null) return 'Sem taxa calculada para este papel.';
    const suffix = this.isentoIr() ? 'isento de IR' : 'já descontado o IR';
    if (this.pctOfCdi() === null) return `líquido, ${suffix}`;
    return `${net.toFixed(2)}% a.a. líquido, ${suffix}`;
  });

  contractedLabel(): string {
    const rate = this.contractedRate();
    if (rate === null) return '—';
    switch (this.rateKind()) {
      case 'pos_fixado':
        return `${rate.toFixed(0)}% do CDI`;
      case 'hibrido':
        return `IPCA + ${rate.toFixed(2)}%`;
      default:
        return `${rate.toFixed(2)}% a.a.`;
    }
  }

  liquidezLabel(): string {
    return this.liquidez() === 'diaria' ? 'Diária' : 'No vencimento';
  }

  irLabel(): string {
    if (this.isentoIr()) return 'Isento';
    const a = this.irAliquotaPct();
    return a === null ? '—' : `${a.toFixed(1)}% sobre o rendimento`;
  }

  ariaLabel(): string {
    return `${this.label()}: ${this.headline()}, ${this.subline()}`;
  }
}
