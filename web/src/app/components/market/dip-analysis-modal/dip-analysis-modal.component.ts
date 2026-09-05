import { CommonModule } from '@angular/common';
import { ProvenanceComponent } from '../../provenance/provenance.component';
import {
  AfterViewInit,
  Component,
  ElementRef,
  HostListener,
  OnDestroy,
  input,
  output,
  viewChild,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { DialogDirective, DipAnalysisResponse } from '../../../core';
import { DipDiagnosisComponent } from '../../dip-diagnosis/dip-diagnosis.component';

@Component({
  selector: 'app-dip-analysis-modal',
  standalone: true,
  imports: [
    CommonModule,
    DialogDirective,
    DipDiagnosisComponent,
    LucideAngularModule,
    RouterLink,
    ProvenanceComponent,
  ],
  template: `
    <div
      class="fixed inset-0 z-drawer fi-overlay"
      (click)="closeAnalysis()"
      aria-hidden="true"
    ></div>

    <div
      fiDialog
      class="fixed top-0 right-0 bottom-0 z-drawer-panel w-full max-w-[600px] bg-ground-1 border-l border-hairline shadow-drawer overflow-y-auto fi-drawer-enter"
      role="dialog"
      aria-modal="true"
      [attr.aria-label]="'Diagnóstico da queda de ' + (analysis()?.symbol ?? '')"
      (keydown.escape)="closeAnalysis()"
      tabindex="-1"
      #panel
    >
      @if (analysis(); as a) {
        <header
          class="sticky top-0 bg-ground-1 border-b border-hairline px-5 py-4 flex items-start justify-between gap-4"
        >
          <div class="min-w-0">
            <p class="fi-eyebrow text-ink-3 m-0">Por que caiu</p>
            <h2 class="fi-title text-ink m-0 mt-0.5">
              {{ a.symbol }}
              @if (a.name) {
                <span class="fi-caption text-ink-3">· {{ a.name }}</span>
              }
            </h2>
          </div>
          <button
            type="button"
            (click)="closeAnalysis()"
            class="btn-icon btn-icon-quiet"
            aria-label="Fechar diagnóstico"
          >
            <lucide-icon name="x" size="18"></lucide-icon>
          </button>
        </header>

        <div class="px-5 py-5">
          <app-dip-diagnosis
            [verdict]="a.verdict"
            [dropPct]="a.drop_from_52w_high_pct"
            [marginPct]="marginPct(a)"
            [reasonGroups]="a.reason_groups"
            [disclaimer]="a.disclaimer"
          />

          <div class="mt-6 pt-5 border-t border-hairline flex flex-wrap gap-3">
            <a
              [routerLink]="['/ativo', a.symbol]"
              class="btn-primary no-underline"
              (click)="closeAnalysis()"
            >
              Abrir a página do ativo
            </a>
          </div>
        </div>
      }
    </div>

    <app-provenance
      method="Separa a queda em três leituras — movimento de mercado, mudança de fundamento e ruído de curto prazo — comparando a série contra as médias móveis e os indicadores do trimestre."
      source="Série de preços e fundamentos da BRAPI."
      limitation="Queda recente não vira fundamento na hora: o balanço só sai semanas depois. A leitura pode estar olhando um número que ainda não mudou."
    ></app-provenance>
  `,
})
export class DipAnalysisModalComponent implements AfterViewInit, OnDestroy {
  readonly analysis = input<DipAnalysisResponse | null>(null);
  readonly close = output<void>();

  private readonly panel = viewChild<ElementRef<HTMLElement>>('panel');
  private readonly openedFrom = document.activeElement as HTMLElement | null;

  ngAfterViewInit(): void {
    this.panel()?.nativeElement.focus();
  }

  ngOnDestroy(): void {
    this.openedFrom?.focus?.();
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.closeAnalysis();
  }

  closeAnalysis(): void {
    this.close.emit();
  }

  marginPct(a: DipAnalysisResponse): number | null {
    const m = a.fair_price?.margin_of_safety;
    return m == null ? null : m * 100;
  }
}
