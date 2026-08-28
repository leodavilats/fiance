import { CommonModule } from '@angular/common';
import { Component, computed, ElementRef, input, signal, viewChild } from '@angular/core';
import { BenchmarkPoint } from '../../core';

interface SeriesPoint {
  x: number;
  y: number;
}

const VB_WIDTH = 640;
const VB_HEIGHT = 220;
const PAD_LEFT = 44;
const PAD_RIGHT = 12;
const PAD_TOP = 16;
const PAD_BOTTOM = 30;

@Component({
  selector: 'app-benchmark-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (points().length < 2) {
      <div class="flex flex-col items-center justify-center gap-2 py-8 text-center text-ink-2">
        <p class="text-sm m-0">Ainda não há histórico suficiente para comparar com benchmarks.</p>
      </div>
    } @else {
      <div class="relative select-none">
        <svg
          #svgRoot
          class="w-full block"
          [attr.viewBox]="'0 0 ' + vbWidth + ' ' + vbHeight"
          preserveAspectRatio="xMidYMid meet"
          (pointermove)="onPointerMove($event)"
          (pointerleave)="onPointerLeave()"
          role="img"
          [attr.aria-label]="ariaLabel()"
        >
          @for (gy of gridLines(); track gy.y) {
            <line
              [attr.x1]="padLeft"
              [attr.y1]="gy.y"
              [attr.x2]="vbWidth - padRight"
              [attr.y2]="gy.y"
              stroke="var(--fi-hairline)"
              stroke-opacity="0.6"
              stroke-width="1"
            />
            <text
              [attr.x]="padLeft - 6"
              [attr.y]="gy.y + 3"
              text-anchor="end"
              class="text-[9px]"
              fill="var(--fi-ink-2)"
            >
              {{ gy.value | number: '1.0-1' }}%
            </text>
          }

          <path
            [attr.d]="pathFor(cdiSeries())"
            stroke="var(--fi-ink-2)"
            stroke-width="1.5"
            fill="none"
            stroke-dasharray="4,3"
          />
          @if (ibovAvailable()) {
            <path
              [attr.d]="pathFor(ibovSeries())"
              stroke="var(--fi-state-attention)"
              stroke-width="1.5"
              fill="none"
            />
          }
          <path
            [attr.d]="pathFor(portfolioSeries())"
            stroke="var(--fi-brand)"
            stroke-width="2.5"
            fill="none"
          />

          @if (hoverIndex() !== null) {
            <line
              [attr.x1]="portfolioSeries()[hoverIndex()!].x"
              [attr.y1]="padTop"
              [attr.x2]="portfolioSeries()[hoverIndex()!].x"
              [attr.y2]="vbHeight - padBottom"
              stroke="var(--fi-ink-2)"
              stroke-opacity="0.45"
              stroke-width="1"
              stroke-dasharray="3,3"
            />
            <circle
              [attr.cx]="portfolioSeries()[hoverIndex()!].x"
              [attr.cy]="portfolioSeries()[hoverIndex()!].y"
              r="4"
              fill="var(--fi-brand)"
              stroke="var(--fi-ground-1)"
              stroke-width="2"
            />
          }
        </svg>

        @if (hoverIndex() !== null) {
          <div
            class="pointer-events-none absolute z-10 rounded-lg border border-hairline bg-ground-1 px-3 py-2 text-xs shadow-popover"
            [style.left.%]="tooltipLeftPct()"
            [style.top]="'8%'"
            [style.transform]="tooltipTransform()"
          >
            <div class="text-ink-2 mb-1">{{ points()[hoverIndex()!].date }}</div>
            <div class="flex items-center gap-1.5 text-ink font-semibold">
              <span
                class="inline-block w-2.5 h-0.5 rounded"
                style="background: var(--fi-brand)"
              ></span>
              Carteira: {{ points()[hoverIndex()!].portfolio_pct | number: '1.1-1' }}%
            </div>
            <div class="flex items-center gap-1.5 text-ink">
              <span
                class="inline-block w-2.5 h-0.5 rounded"
                style="background: var(--fi-ink-2)"
              ></span>
              CDI: {{ points()[hoverIndex()!].cdi_pct | number: '1.1-1' }}%
            </div>
            @if (points()[hoverIndex()!].ibov_pct != null) {
              <div class="flex items-center gap-1.5 text-ink">
                <span
                  class="inline-block w-2.5 h-0.5 rounded"
                  style="background: var(--fi-state-attention)"
                ></span>
                Ibovespa: {{ points()[hoverIndex()!].ibov_pct | number: '1.1-1' }}%
              </div>
            }
          </div>
        }
      </div>

      <div class="flex items-center gap-4 mt-3 text-xs text-ink-2 flex-wrap">
        <span class="flex items-center gap-1.5"
          ><span class="inline-block w-3 h-0.5 rounded" style="background: var(--fi-brand)"></span>
          Carteira</span
        >
        <span class="flex items-center gap-1.5"
          ><span class="inline-block w-3 h-0.5 rounded" style="background: var(--fi-ink-2)"></span>
          CDI</span
        >
        @if (ibovAvailable()) {
          <span class="flex items-center gap-1.5"
            ><span
              class="inline-block w-3 h-0.5 rounded"
              style="background: var(--fi-state-attention)"
            ></span>
            Ibovespa</span
          >
        } @else {
          <span class="text-[11px] opacity-70">Ibovespa indisponível no momento</span>
        }
      </div>

      <!--
        A alternativa textual do gráfico.

        O aria-label do SVG resume — diz que a carteira foi de X a Y — mas
        resumo não é o dado. Quem usa leitor de tela precisa poder comparar
        ponto a ponto, e quem enxerga também quer o número exato de vez em
        quando. A mesma tabela serve aos dois.
      -->
      <button
        type="button"
        class="text-xs text-ink-2 hover:text-ink mt-3 cursor-pointer bg-transparent border-0 p-0 underline decoration-dotted"
        [attr.aria-expanded]="showTable()"
        (click)="showTable.set(!showTable())"
      >
        {{ showTable() ? 'Ocultar a série em tabela' : 'Ver a série em tabela' }}
      </button>

      @if (showTable()) {
        <div class="mt-2 max-h-64 overflow-y-auto rounded-lg border border-hairline">
          <table class="w-full text-xs">
            <caption class="sr-only">
              Retorno acumulado da carteira, do CDI e do Ibovespa em cada data
            </caption>
            <thead class="sticky top-0 bg-ground-2">
              <tr>
                <th scope="col" class="text-left px-2 py-1 font-medium text-ink-2">Data</th>
                <th scope="col" class="text-right px-2 py-1 font-medium text-ink-2">Carteira</th>
                <th scope="col" class="text-right px-2 py-1 font-medium text-ink-2">CDI</th>
                @if (ibovAvailable()) {
                  <th scope="col" class="text-right px-2 py-1 font-medium text-ink-2">Ibovespa</th>
                }
              </tr>
            </thead>
            <tbody>
              @for (p of points(); track p.date) {
                <tr class="border-t border-hairline">
                  <td class="px-2 py-1 text-ink-2">{{ p.date }}</td>
                  <td class="px-2 py-1 text-right text-ink">
                    {{ p.portfolio_pct | number: '1.1-1' }}%
                  </td>
                  <td class="px-2 py-1 text-right text-ink">{{ p.cdi_pct | number: '1.1-1' }}%</td>
                  @if (ibovAvailable()) {
                    <td class="px-2 py-1 text-right text-ink">
                      @if (p.ibov_pct != null) {
                        {{ p.ibov_pct | number: '1.1-1' }}%
                      } @else {
                        —
                      }
                    </td>
                  }
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    }
  `,
})
export class BenchmarkChartComponent {
  points = input.required<BenchmarkPoint[]>();
  ibovAvailable = input<boolean>(false);

  private svgRoot = viewChild<ElementRef<SVGSVGElement>>('svgRoot');

  readonly vbWidth = VB_WIDTH;
  readonly vbHeight = VB_HEIGHT;
  readonly padLeft = PAD_LEFT;
  readonly padRight = PAD_RIGHT;
  readonly padTop = PAD_TOP;
  readonly padBottom = PAD_BOTTOM;

  hoverIndex = signal<number | null>(null);
  readonly showTable = signal(false);

  private plotWidth = VB_WIDTH - PAD_LEFT - PAD_RIGHT;
  private plotHeight = VB_HEIGHT - PAD_TOP - PAD_BOTTOM;

  private allValues = computed(() => {
    const pts = this.points();
    const values = [
      ...pts.map(p => p.portfolio_pct),
      ...pts.map(p => p.cdi_pct),
      ...pts.filter(p => p.ibov_pct != null).map(p => p.ibov_pct as number),
    ];
    return values;
  });

  private minValue = computed(() => Math.min(0, ...this.allValues()));
  private maxValue = computed(() => Math.max(0, ...this.allValues()));

  private toXY(values: (number | null)[]): SeriesPoint[] {
    const min = this.minValue();
    const max = this.maxValue();
    const range = max - min || 1;
    const xStep = this.plotWidth / (values.length - 1);
    return values.map((v, i) => ({
      x: PAD_LEFT + i * xStep,
      y: PAD_TOP + this.plotHeight - (((v ?? 0) - min) / range) * this.plotHeight,
    }));
  }

  portfolioSeries = computed<SeriesPoint[]>(() =>
    this.toXY(this.points().map(p => p.portfolio_pct))
  );
  cdiSeries = computed<SeriesPoint[]>(() => this.toXY(this.points().map(p => p.cdi_pct)));
  ibovSeries = computed<SeriesPoint[]>(() => this.toXY(this.points().map(p => p.ibov_pct)));

  pathFor(pts: SeriesPoint[]): string {
    if (!pts.length) return '';
    return `M ${pts.map(p => `${p.x},${p.y}`).join(' L ')}`;
  }

  gridLines = computed(() => {
    const min = this.minValue();
    const max = this.maxValue();
    if (max === min) return [{ y: PAD_TOP + this.plotHeight / 2, value: max }];
    const steps = 4;
    const lines: { y: number; value: number }[] = [];
    for (let i = 0; i <= steps; i++) {
      const value = min + ((max - min) * i) / steps;
      const y = PAD_TOP + this.plotHeight - (i / steps) * this.plotHeight;
      lines.push({ y, value });
    }
    return lines;
  });

  ariaLabel = computed(() => {
    const pts = this.points();
    if (pts.length < 2) return 'Gráfico comparativo de rentabilidade';
    const last = pts[pts.length - 1];
    return `Comparativo de rentabilidade: carteira ${last.portfolio_pct.toFixed(1)}% vs CDI ${last.cdi_pct.toFixed(1)}%`;
  });

  tooltipLeftPct = computed(() => {
    const idx = this.hoverIndex();
    if (idx === null) return 0;
    return (this.portfolioSeries()[idx].x / this.vbWidth) * 100;
  });

  tooltipTransform = computed(() => {
    const idx = this.hoverIndex();
    if (idx === null) return '';
    const pts = this.points();
    const nearStart = idx < pts.length * 0.2;
    const nearEnd = idx > pts.length * 0.8;
    const xShift = nearStart ? '0%' : nearEnd ? '-100%' : '-50%';
    return `translate(${xShift}, 0)`;
  });

  onPointerMove(event: PointerEvent): void {
    const svg = this.svgRoot()?.nativeElement;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const scaleX = this.vbWidth / rect.width;
    const localX = (event.clientX - rect.left) * scaleX;
    this.hoverIndex.set(this.nearestIndex(localX));
  }

  onPointerLeave(): void {
    this.hoverIndex.set(null);
  }

  private nearestIndex(x: number): number {
    const pts = this.portfolioSeries();
    if (!pts.length) return 0;
    let closest = 0;
    let closestDist = Infinity;
    for (let i = 0; i < pts.length; i++) {
      const dist = Math.abs(pts[i].x - x);
      if (dist < closestDist) {
        closestDist = dist;
        closest = i;
      }
    }
    return closest;
  }
}
