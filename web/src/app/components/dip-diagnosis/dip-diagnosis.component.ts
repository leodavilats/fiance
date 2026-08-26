import { CommonModule } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { DipVerdict, FiState, fiDipDiagnosis, stateTextClass } from '../../core';
import { MarginOfSafetyComponent } from '../margin-of-safety/margin-of-safety.component';
import { ProvenanceComponent } from '../provenance/provenance.component';

/**
 * "Por que caiu?" — a pergunta que separa desconto de deterioração.
 *
 * Queda não é oportunidade por si. O componente separa deliberadamente:
 *
 * 1. **queda aritmética** — quanto o preço recuou do topo de 52 semanas;
 * 2. **valuation** — o preço ficou abaixo do justo, ou o justo é que caiu junto;
 * 3. **fundamento** — o que a qualidade da empresa diz;
 * 4. **conclusão** — a classe da queda, com o critério explícito;
 * 5. **insuficiência** — o que o sistema não conseguiu avaliar.
 *
 * Nada aqui é calculado: classe, motivos e pontuações vêm de
 * `analysis/dip_analysis.py`. O componente escolhe a ordem de leitura.
 */

type DiagnosisKey = keyof typeof fiDipDiagnosis;

const VERDICT_TO_DIAGNOSIS: Record<DipVerdict, DiagnosisKey> = {
  OPORTUNIDADE: 'healthy',
  NEUTRO: 'investigate',
  ARMADILHA: 'structural',
};

/** Ordem de leitura das dimensões — do preço para o fundamento. */
const DIMENSIONS: readonly { key: string; label: string; question: string }[] = [
  { key: 'technical', label: 'Movimento do preço', question: 'quanto caiu, e de onde' },
  { key: 'value', label: 'Preço contra valor', question: 'ficou barato ou só ficou menor' },
  { key: 'quality', label: 'Fundamento', question: 'a empresa piorou junto com o preço' },
  { key: 'dividend', label: 'Proventos', question: 'quanto paga enquanto você espera' },
  { key: 'news', label: 'Notícias', question: 'houve fato novo relevante' },
];

@Component({
  selector: 'app-dip-diagnosis',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, MarginOfSafetyComponent, ProvenanceComponent],
  template: `
    <section>
      <p class="fi-eyebrow text-ink-3 m-0 mb-2">Diagnóstico da queda</p>
      <h3 class="fi-verdict text-ink m-0 flex items-start gap-2">
        <lucide-icon
          [name]="icon()"
          size="18"
          class="mt-1 shrink-0"
          [class]="stateClass()"
          aria-hidden="true"
        ></lucide-icon>
        <span>{{ diagnosis().label }}</span>
      </h3>
      <p class="fi-body text-ink-2 m-0 mt-1">{{ diagnosis().criterion }}.</p>

      <div class="mt-5 grid gap-4 sm:grid-cols-2">
        <div>
          <p class="fi-eyebrow text-ink-3 m-0 mb-1">Queda do topo de 52 semanas</p>
          @if (dropPct() !== null) {
            <p class="fi-metric text-ink m-0">
              −<span class="fi-num">{{ dropPct() | number: '1.1-1' }}</span
              >%
            </p>
            <p class="fi-caption text-ink-3 m-0 mt-1">
              Aritmética do preço — por si só não diz se está barato.
            </p>
          } @else {
            <p class="fi-metric-sm text-indeterminate m-0">—</p>
            <p class="fi-caption text-indeterminate m-0 mt-1">Sem histórico de 52 semanas.</p>
          }
        </div>

        <div>
          <p class="fi-eyebrow text-ink-3 m-0 mb-1">Distância do preço justo</p>
          <app-margin-of-safety
            [marginPct]="marginPct()"
            reason="Sem método de valuation aplicável a este ativo."
          />
        </div>
      </div>

      <div class="mt-5 border-t border-hairline">
        @for (dim of dimensions(); track dim.key) {
          <details class="fi-dim border-b border-hairline">
            <summary
              class="flex items-baseline justify-between gap-3 py-3 cursor-pointer list-none fi-focusable"
            >
              <span class="fi-title text-ink">{{ dim.label }}</span>
              <span class="fi-caption text-ink-3">{{ dim.question }} →</span>
            </summary>
            <ul class="list-none m-0 p-0 pb-3 flex flex-col gap-1">
              @for (reason of dim.reasons; track reason) {
                <li class="fi-body text-ink-2">{{ reason }}</li>
              }
            </ul>
          </details>
        }
      </div>

      @if (unavailable().length > 0) {
        <p class="fi-caption text-indeterminate m-0 mt-3">
          Não foi possível avaliar: {{ unavailable().join(' · ') }}.
        </p>
      }

      <app-provenance
        method="Diagnóstico de queda: valor, qualidade, técnico, proventos e notícias, ponderados em backend/app/analysis/dip_analysis.py."
        [source]="'Cotações e fundamentos via BRAPI.'"
        [limitation]="disclaimer()"
      />
    </section>
  `,
  styles: [
    `
      .fi-dim > summary::-webkit-details-marker {
        display: none;
      }
      .fi-dim > summary:hover .fi-caption {
        color: var(--fi-ink-2);
      }
    `,
  ],
})
export class DipDiagnosisComponent {
  readonly verdict = input.required<DipVerdict>();
  /** Queda em relação ao topo de 52 semanas, em % positivo. */
  readonly dropPct = input<number | null>(null);
  /** Margem de segurança em %, do backend. */
  readonly marginPct = input<number | null>(null);
  readonly reasonGroups = input<Record<string, string[]>>({});
  readonly disclaimer = input(
    'Leitura do sistema sobre dados públicos, não recomendação de compra.'
  );

  readonly diagnosis = computed(() => fiDipDiagnosis[VERDICT_TO_DIAGNOSIS[this.verdict()]]);

  readonly dimensions = computed(() =>
    DIMENSIONS.map(d => ({ ...d, reasons: this.reasonGroups()[d.key] ?? [] })).filter(
      d => d.reasons.length > 0
    )
  );

  /** O que o sistema declarou não ter — some da evidência, vira estado (§11). */
  readonly unavailable = computed(() =>
    Object.values(this.reasonGroups())
      .flat()
      .filter(r => r.toLowerCase().includes('indisponível'))
      .map(r => r.replace(/\s*indisponível\.?$/i, ''))
  );

  icon(): string {
    switch (this.state()) {
      case 'favorable':
        return 'circle-check';
      case 'attention':
        return 'triangle-alert';
      default:
        return 'circle-alert';
    }
  }

  state(): FiState {
    return this.diagnosis().state;
  }

  stateClass(): string {
    return stateTextClass(this.state());
  }
}
