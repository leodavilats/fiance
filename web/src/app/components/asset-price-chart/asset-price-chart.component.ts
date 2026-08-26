import { CommonModule } from '@angular/common';
import { Component, computed, ElementRef, input, signal, viewChild } from '@angular/core';
import { PricePoint } from '../../core';
import { EmptyStateComponent } from '../empty-state/empty-state.component';

/**
 * "O preço está longe do justo?"
 *
 * É a pergunta que o gráfico existe para responder, e por isso ele nunca é só
 * a linha do preço: as duas linhas de referência — **preço justo** e **seu
 * preço médio** — são o que transforma uma curva em decisão. Cada uma tem
 * semântica visual própria: o justo é tracejado (é estimativa), o seu preço
 * médio é pontilhado (é fato, mas seu, não do mercado), e o preço é sólido.
 *
 * Sem série não há gráfico: aparece o estado de insuficiência, nunca uma linha
 * reta inventada.
 */

interface Plotted {
  readonly x: number;
  readonly y: number;
  readonly close: number;
  readonly date: string;
}

interface Period {
  readonly id: string;
  readonly label: string;
  readonly days: number;
}

const PERIODS: readonly Period[] = [
  { id: '1m', label: '1 mês', days: 30 },
  { id: '6m', label: '6 meses', days: 182 },
  { id: '1a', label: '1 ano', days: 365 },
  { id: '2a', label: '2 anos', days: 730 },
];

const VB_WIDTH = 640;
const VB_HEIGHT = 240;
const PAD_LEFT = 56;
const PAD_RIGHT = 64;
const PAD_TOP = 16;
const PAD_BOTTOM = 30;

/** Abaixo disso não há forma: dois pontos são um segmento, não uma tendência. */
const MIN_POINTS = 5;

@Component({
  selector: 'app-asset-price-chart',
  standalone: true,
  imports: [CommonModule, EmptyStateComponent],
  template: `
    <section>
      <div class="flex items-baseline justify-between gap-3 flex-wrap mb-1">
        <h3 class="fi-title text-ink m-0">O preço está longe do valor justo?</h3>
        <div class="flex items-center gap-1" role="group" aria-label="Período do gráfico">
          @for (p of periods; track p.id) {
            <button
              type="button"
              class="subtab-btn"
              [class.active]="p.id === period()"
              [attr.aria-pressed]="p.id === period()"
              (click)="period.set(p.id)"
            >
              {{ p.label }}
            </button>
          }
        </div>
      </div>

      @if (visible().length < MIN_POINTS) {
        <app-empty-state
          icon="chart-line"
          title="Histórico curto demais para desenhar"
          reason="A fonte devolveu menos de {{
            MIN_POINTS
          }} fechamentos neste período — com tão poucos pontos, qualquer linha sugeriria uma tendência que os dados não sustentam."
          nextStep="Períodos mais longos costumam ter cobertura melhor."
          actionLabel="Ver 2 anos"
          (action)="period.set('2a')"
        />
      } @else {
        <p class="fi-caption text-ink-3 m-0 mb-3">
          Fechamento diário, em reais · {{ rangeLabel() }} · fonte BRAPI
        </p>

        <div class="relative select-none">
          <svg
            #svgRoot
            class="w-full block"
            [attr.viewBox]="'0 0 ' + vbWidth + ' ' + vbHeight"
            preserveAspectRatio="xMidYMid meet"
            (pointermove)="onPointerMove($event)"
            (pointerleave)="hover.set(null)"
            (blur)="hover.set(null)"
            (keydown)="onKeydown($event)"
            tabindex="0"
            role="img"
            [attr.aria-label]="ariaLabel()"
          >
            <line
              [attr.x1]="padLeft"
              [attr.x2]="vbWidth - padRight"
              [attr.y1]="vbHeight - padBottom"
              [attr.y2]="vbHeight - padBottom"
              stroke="var(--fi-hairline)"
              stroke-width="1"
            />

            @for (tick of yTicks(); track tick.value) {
              <text
                [attr.x]="padLeft - 8"
                [attr.y]="tick.y + 4"
                text-anchor="end"
                fill="var(--fi-ink-3)"
                font-size="11"
              >
                {{ tick.value | number: '1.0-2' }}
              </text>
            }

            @if (fairY() !== null) {
              <line
                [attr.x1]="padLeft"
                [attr.x2]="vbWidth - padRight"
                [attr.y1]="fairY()"
                [attr.y2]="fairY()"
                stroke="var(--fi-brand)"
                stroke-width="1.5"
                stroke-dasharray="6 4"
              />
              <text
                [attr.x]="vbWidth - padRight + 6"
                [attr.y]="fairY()! + 4"
                fill="var(--fi-brand)"
                font-size="11"
              >
                justo
              </text>
            }

            @if (avgY() !== null) {
              <line
                [attr.x1]="padLeft"
                [attr.x2]="vbWidth - padRight"
                [attr.y1]="avgY()"
                [attr.y2]="avgY()"
                stroke="var(--fi-ink-2)"
                stroke-width="1.5"
                stroke-dasharray="2 3"
              />
              <text
                [attr.x]="vbWidth - padRight + 6"
                [attr.y]="avgY()! + 4"
                fill="var(--fi-ink-2)"
                font-size="11"
              >
                seu
              </text>
            }

            <path
              [attr.d]="linePath()"
              fill="none"
              stroke="var(--fi-ink-1)"
              stroke-width="1.75"
              stroke-linejoin="round"
              stroke-linecap="round"
            />

            @if (hovered(); as h) {
              <line
                [attr.x1]="h.x"
                [attr.x2]="h.x"
                [attr.y1]="padTop"
                [attr.y2]="vbHeight - padBottom"
                stroke="var(--fi-hairline-strong)"
                stroke-width="1"
              />
              <circle
                [attr.cx]="h.x"
                [attr.cy]="h.y"
                r="3.5"
                fill="var(--fi-ink-1)"
                stroke="var(--fi-ground-1)"
                stroke-width="1.5"
              />
            }

            <text [attr.x]="padLeft" [attr.y]="vbHeight - 10" fill="var(--fi-ink-3)" font-size="11">
              {{ firstLabel() }}
            </text>
            <text
              [attr.x]="vbWidth - padRight"
              [attr.y]="vbHeight - 10"
              text-anchor="end"
              fill="var(--fi-ink-3)"
              font-size="11"
            >
              {{ lastLabel() }}
            </text>
          </svg>

          @if (hovered(); as h) {
            <div
              class="pointer-events-none absolute rounded-md border border-hairline bg-ground-1 px-3 py-2 shadow-popover"
              [style.left.%]="(h.x / vbWidth) * 100"
              [style.top.%]="(h.y / vbHeight) * 100"
              style="transform: translate(-50%, -120%)"
              role="status"
            >
              <p class="fi-caption text-ink-3 m-0">{{ dateLabel(h.date) }}</p>
              <p class="fi-metric-sm text-ink m-0">{{ h.close | currency: 'BRL' }}</p>
              @if (fairPrice(); as fair) {
                <p class="fi-caption text-ink-3 m-0 mt-0.5">
                  {{ distanceLabel(h.close, fair) }}
                </p>
              }
            </div>
          }
        </div>

        <ul class="list-none m-0 p-0 mt-3 flex flex-wrap gap-x-5 gap-y-1 fi-caption text-ink-3">
          <li class="flex items-center gap-1.5">
            <span class="inline-block w-4 h-[2px] bg-ink"></span> preço de fechamento
          </li>
          @if (fairPrice() !== null) {
            <li class="flex items-center gap-1.5">
              <span class="inline-block w-4 border-t-2 border-dashed border-brand"></span>
              preço justo estimado ({{ fairPrice() | currency: 'BRL' }})
            </li>
          }
          @if (averagePrice() !== null) {
            <li class="flex items-center gap-1.5">
              <span class="inline-block w-4 border-t-2 border-dotted border-ink-2"></span>
              seu preço médio ({{ averagePrice() | currency: 'BRL' }})
            </li>
          }
        </ul>

        <button
          type="button"
          class="fi-caption text-ink-3 hover:text-ink-2 mt-3 cursor-pointer bg-transparent border-0 p-0 underline decoration-dotted"
          (click)="showTable.set(!showTable())"
        >
          {{ showTable() ? 'Ocultar a série em tabela' : 'Ver a série em tabela' }}
        </button>

        @if (showTable()) {
          <div class="mt-2 max-h-64 overflow-y-auto border border-hairline rounded-md">
            <table class="w-full">
              <caption class="sr-only">
                Fechamentos diários do período selecionado
              </caption>
              <thead class="sticky top-0 bg-ground-2">
                <tr>
                  <th class="text-left px-3 py-1.5 fi-caption text-ink-3 font-medium">Data</th>
                  <th class="text-right px-3 py-1.5 fi-caption text-ink-3 font-medium">
                    Fechamento
                  </th>
                </tr>
              </thead>
              <tbody>
                @for (p of visible(); track p.date) {
                  <tr class="border-t border-hairline">
                    <td class="px-3 py-1 fi-caption text-ink-2">{{ dateLabel(p.date) }}</td>
                    <td class="px-3 py-1 fi-caption text-ink text-right fi-num">
                      {{ p.close | currency: 'BRL' }}
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }
      }
    </section>
  `,
  styles: [
    `
      svg:focus-visible {
        outline: var(--fi-focus-ring) solid var(--fi-brand);
        outline-offset: var(--fi-focus-offset);
      }
      .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
      }
    `,
  ],
})
export class AssetPriceChartComponent {
  readonly history = input.required<readonly PricePoint[]>();
  /** Consenso de preço justo, do backend. `null` quando nenhum método se aplica. */
  readonly fairPrice = input<number | null>(null);
  /** Preço médio da posição, quando o ativo está na carteira. */
  readonly averagePrice = input<number | null>(null);

  readonly periods = PERIODS;
  readonly period = signal<string>('1a');
  readonly hover = signal<number | null>(null);
  readonly showTable = signal(false);

  readonly vbWidth = VB_WIDTH;
  readonly vbHeight = VB_HEIGHT;
  readonly padLeft = PAD_LEFT;
  readonly padRight = PAD_RIGHT;
  readonly padTop = PAD_TOP;
  readonly padBottom = PAD_BOTTOM;
  readonly MIN_POINTS = MIN_POINTS;

  private readonly svgRoot = viewChild<ElementRef<SVGSVGElement>>('svgRoot');

  readonly visible = computed(() => {
    const days = PERIODS.find(p => p.id === this.period())?.days ?? 365;
    const all = [...this.history()].sort((a, b) => a.date.localeCompare(b.date));
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);
    const iso = cutoff.toISOString().slice(0, 10);
    const windowed = all.filter(p => p.date >= iso);
    return windowed.length >= MIN_POINTS ? windowed : all;
  });

  /**
   * A escala inclui as linhas de referência de propósito: um preço justo fora
   * da faixa desenhada seria uma linha invisível — e a comparação some.
   */
  private readonly scale = computed(() => {
    const closes = this.visible().map(p => p.close);
    const anchors = [this.fairPrice(), this.averagePrice()].filter(
      (v): v is number => v !== null && v > 0
    );
    const values = [...closes, ...anchors];
    const min = Math.min(...values);
    const max = Math.max(...values);
    const pad = (max - min) * 0.08 || Math.max(max * 0.02, 0.01);
    return { min: min - pad, max: max + pad };
  });

  private y(value: number): number {
    const { min, max } = this.scale();
    const plot = VB_HEIGHT - PAD_TOP - PAD_BOTTOM;
    const ratio = max === min ? 0.5 : (value - min) / (max - min);
    return PAD_TOP + plot * (1 - ratio);
  }

  readonly plotted = computed<Plotted[]>(() => {
    const points = this.visible();
    const plotWidth = VB_WIDTH - PAD_LEFT - PAD_RIGHT;
    const step = points.length > 1 ? plotWidth / (points.length - 1) : 0;
    return points.map((p, i) => ({
      x: PAD_LEFT + step * i,
      y: this.y(p.close),
      close: p.close,
      date: p.date,
    }));
  });

  readonly linePath = computed(() =>
    this.plotted()
      .map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(2)} ${p.y.toFixed(2)}`)
      .join(' ')
  );

  readonly fairY = computed(() => {
    const fair = this.fairPrice();
    return fair === null || fair <= 0 ? null : this.y(fair);
  });

  readonly avgY = computed(() => {
    const avg = this.averagePrice();
    return avg === null || avg <= 0 ? null : this.y(avg);
  });

  readonly yTicks = computed(() => {
    const { min, max } = this.scale();
    return [max, (max + min) / 2, min].map(value => ({ value, y: this.y(value) }));
  });

  readonly hovered = computed(() => {
    const i = this.hover();
    return i === null ? null : (this.plotted()[i] ?? null);
  });

  readonly firstLabel = computed(() => this.dateLabel(this.visible()[0]?.date ?? ''));
  readonly lastLabel = computed(() =>
    this.dateLabel(this.visible()[this.visible().length - 1]?.date ?? '')
  );

  readonly rangeLabel = computed(() => `${this.firstLabel()} a ${this.lastLabel()}`);

  onPointerMove(event: PointerEvent): void {
    const svg = this.svgRoot()?.nativeElement;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const ratio = (event.clientX - rect.left) / rect.width;
    const x = ratio * VB_WIDTH;
    const points = this.plotted();
    if (points.length === 0) return;

    let closest = 0;
    for (let i = 1; i < points.length; i += 1) {
      if (Math.abs(points[i].x - x) < Math.abs(points[closest].x - x)) closest = i;
    }
    this.hover.set(closest);
  }

  onKeydown(event: KeyboardEvent): void {
    const total = this.plotted().length;
    if (total === 0) return;
    const current = this.hover() ?? total - 1;
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      this.hover.set(Math.min(total - 1, current + 1));
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault();
      this.hover.set(Math.max(0, current - 1));
    } else if (event.key === 'Escape') {
      this.hover.set(null);
    }
  }

  dateLabel(iso: string): string {
    if (!iso) return '—';
    const date = new Date(`${iso}T12:00:00`);
    if (Number.isNaN(date.getTime())) return iso;
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: '2-digit' });
  }

  distanceLabel(close: number, fair: number): string {
    const pct = ((fair - close) / fair) * 100;
    if (Math.abs(pct) < 0.5) return 'no preço justo estimado';
    return pct > 0
      ? `${pct.toFixed(1)}% abaixo do justo`
      : `${Math.abs(pct).toFixed(1)}% acima do justo`;
  }

  ariaLabel(): string {
    const points = this.visible();
    if (points.length === 0) return 'Sem série de preços disponível.';
    const first = points[0];
    const last = points[points.length - 1];
    const change = ((last.close - first.close) / first.close) * 100;
    const fair = this.fairPrice();
    const fairNote = fair ? ` Preço justo estimado em ${fair.toFixed(2)} reais.` : '';
    return (
      `Preço de ${this.dateLabel(first.date)} a ${this.dateLabel(last.date)}: ` +
      `de ${first.close.toFixed(2)} a ${last.close.toFixed(2)} reais, ` +
      `variação de ${change.toFixed(1)}%.${fairNote}`
    );
  }
}
