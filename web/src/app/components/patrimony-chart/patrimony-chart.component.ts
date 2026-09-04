import { CommonModule } from '@angular/common';
import { Component, computed, ElementRef, input, signal, viewChild } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { PortfolioSnapshot } from '../../core';

interface ChartPoint {
  x: number;
  y: number;
  value: number;
  capturedAt: number;
}

const VB_WIDTH = 640;
const VB_HEIGHT = 220;
const PAD_LEFT = 52;
const PAD_RIGHT = 12;
const PAD_TOP = 16;
const PAD_BOTTOM = 34;

@Component({
  selector: 'app-patrimony-chart',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    @if (snapshots().length === 0) {
      <div class="flex flex-col items-center justify-center gap-2 py-10 text-center text-ink-2">
        <lucide-icon name="chart-column" size="28" class="opacity-40"></lucide-icon>
        <p class="fi-body m-0">Ainda não há histórico suficiente para exibir a evolução.</p>
      </div>
    } @else if (snapshots().length === 1) {
      <div class="flex flex-col items-center justify-center gap-1 py-8 text-center">
        <div class="fi-caption text-ink-2">Único registro até o momento</div>
        <div class="fi-metric-sm text-ink">
          R$ {{ snapshots()[0].total_current | number: '1.0-0' }}
        </div>
        <div class="fi-caption text-ink-2">{{ formatDate(snapshots()[0].captured_at) }}</div>
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
          (focus)="onFocus()"
          (blur)="onPointerLeave()"
          (keydown)="onKeydown($event)"
          tabindex="0"
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
              [attr.x]="padLeft - 8"
              [attr.y]="gy.y + 3"
              text-anchor="end"
              class="text-[9px]"
              fill="var(--fi-ink-2)"
            >
              {{ gy.value | number: '1.0-0' }}
            </text>
          }
          <line
            [attr.x1]="padLeft"
            [attr.y1]="vbHeight - padBottom"
            [attr.x2]="vbWidth - padRight"
            [attr.y2]="vbHeight - padBottom"
            stroke="var(--fi-ink-3)"
            stroke-opacity="0.5"
            stroke-width="1"
          />

          <path [attr.d]="areaPath()" fill="color-mix(in srgb, var(--fi-brand) 12%, transparent)" />

          <path
            [attr.d]="linePath()"
            stroke="var(--fi-brand)"
            stroke-width="2"
            fill="none"
            stroke-linecap="round"
            stroke-linejoin="round"
          />

          @if (hoverIndex() !== null) {
            <line
              [attr.x1]="points()[hoverIndex()!].x"
              [attr.y1]="padTop"
              [attr.x2]="points()[hoverIndex()!].x"
              [attr.y2]="vbHeight - padBottom"
              stroke="var(--fi-ink-2)"
              stroke-opacity="0.45"
              stroke-width="1"
              stroke-dasharray="3,3"
            />
          }

          @for (p of points(); track p.capturedAt; let i = $index) {
            @if (isKeyPoint(i)) {
              <circle
                [attr.cx]="p.x"
                [attr.cy]="p.y"
                r="3"
                fill="var(--fi-brand)"
                stroke="var(--fi-ground-1)"
                stroke-width="1.5"
              />
            }
            @if (hoverIndex() === i) {
              <circle
                [attr.cx]="p.x"
                [attr.cy]="p.y"
                r="5"
                fill="var(--fi-brand)"
                stroke="var(--fi-ground-1)"
                stroke-width="2"
              />
            }
          }

          <text
            [attr.x]="padLeft"
            [attr.y]="vbHeight - 10"
            text-anchor="start"
            class="text-[9px]"
            fill="var(--fi-ink-2)"
          >
            {{ formatDate(snapshots()[0].captured_at) }}
          </text>
          <text
            [attr.x]="vbWidth - padRight"
            [attr.y]="vbHeight - 10"
            text-anchor="end"
            class="text-[9px]"
            fill="var(--fi-ink-2)"
          >
            {{ formatDate(snapshots()[snapshots().length - 1].captured_at) }}
          </text>
        </svg>

        @if (hoverIndex() !== null) {
          <div
            class="fi-caption pointer-events-none absolute z-popover rounded-lg border border-hairline bg-ground-1 px-3 py-2 shadow-popover"
            [style.left.%]="tooltipLeftPct()"
            [style.top.%]="tooltipTopPct()"
            [style.transform]="tooltipTransform()"
          >
            <div class="text-ink-2 mb-0.5">
              {{ formatDate(points()[hoverIndex()!].capturedAt) }}
            </div>
            <div class="fi-label flex items-center gap-1.5 text-ink">
              <span
                class="inline-block w-2.5 h-0.5 rounded"
                style="background: var(--fi-brand)"
              ></span>
              R$ {{ points()[hoverIndex()!].value | number: '1.0-0' }}
            </div>
          </div>
        }
      </div>

      <div class="mt-2">
        <button type="button" class="btn-quiet btn-explain" (click)="showTable.set(!showTable())">
          {{ showTable() ? 'Ocultar dados em tabela' : 'Ver dados em tabela' }}
        </button>
        @if (showTable()) {
          <div class="mt-2 max-h-48 overflow-y-auto border-t border-hairline">
            <table class="fi-caption w-full">
              <thead>
                <tr class="bg-ground-2 text-ink-2">
                  <th class="fi-label text-left px-2 py-1">Data</th>
                  <th class="fi-label text-right px-2 py-1">Patrimônio</th>
                </tr>
              </thead>
              <tbody>
                @for (snap of snapshots(); track snap.captured_at) {
                  <tr class="border-t border-hairline">
                    <td class="px-2 py-1 text-ink">{{ formatDate(snap.captured_at) }}</td>
                    <td class="px-2 py-1 text-right text-ink">
                      R$ {{ snap.total_current | number: '1.0-0' }}
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }
      </div>
    }
  `,
})
export class PatrimonyChartComponent {
  snapshots = input.required<PortfolioSnapshot[]>();

  private svgRoot = viewChild<ElementRef<SVGSVGElement>>('svgRoot');

  readonly vbWidth = VB_WIDTH;
  readonly vbHeight = VB_HEIGHT;
  readonly padLeft = PAD_LEFT;
  readonly padRight = PAD_RIGHT;
  readonly padTop = PAD_TOP;
  readonly padBottom = PAD_BOTTOM;

  hoverIndex = signal<number | null>(null);
  showTable = signal(false);

  private plotWidth = VB_WIDTH - PAD_LEFT - PAD_RIGHT;
  private plotHeight = VB_HEIGHT - PAD_TOP - PAD_BOTTOM;

  private minValue = computed(() => {
    const snaps = this.snapshots();
    if (!snaps.length) return 0;
    return Math.min(...snaps.map(s => s.total_current));
  });

  private maxValue = computed(() => {
    const snaps = this.snapshots();
    if (!snaps.length) return 0;
    return Math.max(...snaps.map(s => s.total_current));
  });

  points = computed<ChartPoint[]>(() => {
    const snaps = this.snapshots();
    if (snaps.length < 2) return [];
    const min = this.minValue();
    const max = this.maxValue();
    const range = max - min || 1;
    const xStep = this.plotWidth / (snaps.length - 1);
    return snaps.map((s, i) => ({
      x: PAD_LEFT + i * xStep,
      y: PAD_TOP + this.plotHeight - ((s.total_current - min) / range) * this.plotHeight,
      value: s.total_current,
      capturedAt: s.captured_at,
    }));
  });

  linePath = computed(() => {
    const pts = this.points();
    if (!pts.length) return '';
    return `M ${pts.map(p => `${p.x},${p.y}`).join(' L ')}`;
  });

  areaPath = computed(() => {
    const pts = this.points();
    if (!pts.length) return '';
    const baseline = this.vbHeight - this.padBottom;
    const first = pts[0];
    const last = pts[pts.length - 1];
    return `M ${first.x},${baseline} L ${pts.map(p => `${p.x},${p.y}`).join(' L ')} L ${last.x},${baseline} Z`;
  });

  gridLines = computed(() => {
    const min = this.minValue();
    const max = this.maxValue();
    if (max === min) {
      return [{ y: PAD_TOP + this.plotHeight / 2, value: max }];
    }
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
    const snaps = this.snapshots();
    if (snaps.length < 2) return 'Gráfico de evolução do patrimônio';
    const first = snaps[0].total_current;
    const last = snaps[snaps.length - 1].total_current;
    return `Gráfico de evolução do patrimônio, de R$ ${Math.round(first)} para R$ ${Math.round(last)} ao longo de ${snaps.length} registros`;
  });

  tooltipLeftPct = computed(() => {
    const idx = this.hoverIndex();
    if (idx === null) return 0;
    return (this.points()[idx].x / this.vbWidth) * 100;
  });

  tooltipTopPct = computed(() => {
    const idx = this.hoverIndex();
    if (idx === null) return 0;
    return (this.points()[idx].y / this.vbHeight) * 100;
  });

  tooltipTransform = computed(() => {
    const idx = this.hoverIndex();
    if (idx === null) return '';
    const pts = this.points();
    const nearStart = idx < pts.length * 0.2;
    const nearEnd = idx > pts.length * 0.8;
    const xShift = nearStart ? '0%' : nearEnd ? '-100%' : '-50%';
    return `translate(${xShift}, -120%)`;
  });

  isKeyPoint(i: number): boolean {
    const len = this.snapshots().length;
    if (len <= 1) return true;
    const step = Math.max(1, Math.floor(len / 8));
    return i === 0 || i === len - 1 || i % step === 0;
  }

  formatDate(timestamp: number): string {
    return new Date(timestamp * 1000).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
    });
  }

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

  onFocus(): void {
    if (this.hoverIndex() === null && this.points().length) {
      this.hoverIndex.set(0);
    }
  }

  onKeydown(event: KeyboardEvent): void {
    const pts = this.points();
    if (!pts.length) return;
    const current = this.hoverIndex() ?? 0;
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      this.hoverIndex.set(Math.min(pts.length - 1, current + 1));
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault();
      this.hoverIndex.set(Math.max(0, current - 1));
    }
  }

  private nearestIndex(x: number): number {
    const pts = this.points();
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
