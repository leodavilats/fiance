import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  DipAnalysisService,
  DipScanItem,
  DipVerdict,
  FiState,
  RecommendService,
  fiDipDiagnosis,
  fiDipScoreBands,
  stateTextClass,
} from '../../../core';
import { EmptyStateComponent } from '../../empty-state/empty-state.component';
import { ScoreRulerComponent } from '../../score-ruler/score-ruler.component';
import { SkeletonComponent } from '../../skeleton/skeleton.component';

const DIAGNOSIS: Record<DipVerdict, keyof typeof fiDipDiagnosis> = {
  OPORTUNIDADE: 'healthy',
  NEUTRO: 'investigate',
  ARMADILHA: 'structural',
};

const RELAXED_MIN_SCORE = 25;

@Component({
  selector: 'app-dip-scanner',
  standalone: true,
  imports: [
    CommonModule,
    EmptyStateComponent,
    LucideAngularModule,
    ReactiveFormsModule,
    RouterLink,
    ScoreRulerComponent,
    SkeletonComponent,
  ],
  template: `
    <div class="max-w-reading">
      <section>
        <h1 class="fi-title text-ink m-0">Quedas recentes</h1>
        <p class="fi-body text-ink-2 m-0 mt-1">
          Queda não é oportunidade por si. Cada item abaixo diz o que caiu, quanto, e se o
          fundamento caiu junto.
        </p>

        <form
          [formGroup]="scanForm"
          (ngSubmit)="runScan()"
          class="flex flex-wrap items-end gap-3 mt-4"
        >
          <div>
            <label for="dip-min-score" class="fi-caption text-ink-3 block mb-1">Score mínimo</label>
            <input
              id="dip-min-score"
              type="number"
              formControlName="min_score"
              class="input w-[110px]"
            />
          </div>
          <div>
            <label for="dip-top" class="fi-caption text-ink-3 block mb-1">Quantos ativos</label>
            <input id="dip-top" type="number" formControlName="top" class="input w-[110px]" />
          </div>
          <div>
            <label for="dip-category" class="fi-caption text-ink-3 block mb-1">Categoria</label>
            <select id="dip-category" formControlName="category" class="input w-[160px]">
              <option value="">Todas</option>
              <option value="acoes_br">Ações BR</option>
              <option value="fiis">FIIs</option>
            </select>
          </div>
          <button type="submit" class="btn-primary" [disabled]="scanning()">
            <lucide-icon
              [name]="scanning() ? 'loader-circle' : 'search'"
              size="14"
              [class.spin]="scanning()"
            ></lucide-icon>
            {{ scanning() ? 'Varrendo…' : 'Buscar quedas' }}
          </button>
        </form>
      </section>

      @if (scanning()) {
        <div class="mt-8 flex flex-col gap-6">
          <app-skeleton shape="verdict" />
          <app-skeleton shape="row" [count]="5" />
        </div>
      } @else if (dipResults(); as dips) {
        @if (dips.items.length === 0) {
          <div class="mt-6">
            <app-empty-state
              icon="search-x"
              title="Nenhuma queda passou pelo filtro"
              reason="Com score mínimo de {{
                minScore()
              }}, nenhum ativo do universo varrido chegou até aqui — o que normalmente significa que não há queda com fundamento preservado no momento."
              nextStep="Baixar o score mínimo mostra quedas mais duvidosas, que exigem leitura mais cuidadosa."
              actionLabel="Buscar com score 25"
              (action)="relaxFilter()"
              secondaryLabel="Ver oportunidades"
              secondaryRoute="/descobrir/oportunidades"
            />
          </div>
        } @else {
          <section class="mt-8">
            <p class="fi-eyebrow text-ink-3 m-0 mb-2">
              {{ dips.items.length }} {{ dips.items.length === 1 ? 'ativo' : 'ativos' }} em baixa
            </p>

            <ul class="list-none m-0 p-0">
              @for (dip of dips.items; track dip.symbol) {
                <li class="py-4 border-t border-hairline">
                  <div class="flex items-start justify-between gap-4">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 flex-wrap">
                        <a
                          [routerLink]="['/ativo', dip.symbol]"
                          class="fi-ticker text-ink no-underline hover:text-brand"
                        >
                          {{ dip.symbol }}
                        </a>
                        <span class="verdict-pill" [class]="dipClass(dip.verdict)">
                          <lucide-icon
                            [name]="dipIcon(dip.verdict)"
                            size="12"
                            aria-hidden="true"
                          ></lucide-icon>
                          {{ dipLabel(dip.verdict) }}
                        </span>
                      </div>
                      @if (dip.name) {
                        <p class="fi-caption text-ink-3 m-0 mt-0.5">{{ dip.name }}</p>
                      }

                      <p class="fi-body text-ink m-0 mt-2">{{ dip.top_reason }}</p>

                      <div class="flex items-center gap-4 mt-2 flex-wrap fi-caption text-ink-3">
                        @if (dip.drop_from_52w_high_pct != null) {
                          <span>
                            Caiu
                            <strong class="fi-num text-ink"
                              >{{ dip.drop_from_52w_high_pct | number: '1.1-1' }}%</strong
                            >
                            do topo de 52 semanas
                          </span>
                        }
                        @if (dip.margin_of_safety != null) {
                          <span>
                            Margem
                            <strong class="fi-num text-ink"
                              >{{ dip.margin_of_safety * 100 | number: '1.0-0' }}%</strong
                            >
                          </span>
                        } @else {
                          <span class="text-indeterminate">Sem preço justo calculável</span>
                        }
                      </div>
                    </div>

                    <div class="shrink-0 w-[132px]">
                      <app-score-ruler
                        [score]="dip.dip_score"
                        [bands]="dipBands"
                        size="list"
                        subject="Leitura da queda"
                      />
                      <button
                        type="button"
                        class="btn-secondary compact-btn mt-2 w-full"
                        (click)="showDipAnalysis(dip.symbol)"
                      >
                        Por que caiu?
                      </button>
                    </div>
                  </div>
                </li>
              }
            </ul>

            <p class="fi-caption text-ink-3 m-0 mt-4 pt-4 border-t border-hairline">
              Leitura do sistema sobre dados públicos, não recomendação de compra.
            </p>
          </section>
        }
      }
    </div>
  `,
})
export class DipScannerComponent implements OnInit {
  private readonly api = inject(RecommendService);
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly dip = inject(DipAnalysisService);

  readonly dipBands = fiDipScoreBands;

  readonly dipResults = signal<{ items: DipScanItem[] } | null>(null);
  readonly scanning = signal(false);

  readonly scanForm = this.fb.nonNullable.group({
    min_score: [40, [Validators.required, Validators.min(0), Validators.max(100)]],
    top: [12, [Validators.required, Validators.min(1), Validators.max(30)]],
    category: [''],
  });

  readonly minScore = computed(() => this.scanForm.getRawValue().min_score);

  ngOnInit(): void {
    const q = this.route.snapshot.queryParamMap;
    this.scanForm.patchValue({
      min_score: Number(q.get('min_score') ?? 40),
      top: Number(q.get('top') ?? 12),
      category: q.get('category') ?? '',
    });
    if (q.keys.length > 0) this.runScan();
  }

  runScan(): void {
    if (this.scanForm.invalid) return;
    const { min_score, top, category } = this.scanForm.getRawValue();

    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { min_score, top, category: category || null },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });

    this.scanning.set(true);
    this.api.dipScanner(min_score, top, undefined, category || undefined).subscribe({
      next: data => {
        this.dipResults.set(data);
        this.scanning.set(false);
      },
      error: () => this.scanning.set(false),
    });
  }

  relaxFilter(): void {
    this.scanForm.patchValue({ min_score: RELAXED_MIN_SCORE });
    this.runScan();
  }

  showDipAnalysis(ticker: string): void {
    this.dip.show(ticker);
  }

  dipLabel(verdict: DipVerdict): string {
    return fiDipDiagnosis[DIAGNOSIS[verdict]].label;
  }

  dipClass(verdict: DipVerdict): string {
    const map: Record<FiState, string> = {
      favorable: 'v-buy',
      attention: 'v-hold',
      adverse: 'v-sell',
      neutral: 'v-unknown',
      indeterminate: 'v-unknown',
    };
    return map[fiDipDiagnosis[DIAGNOSIS[verdict]].state];
  }

  dipIcon(verdict: DipVerdict): string {
    const state = fiDipDiagnosis[DIAGNOSIS[verdict]].state;
    if (state === 'favorable') return 'circle-check';
    if (state === 'attention') return 'triangle-alert';
    return 'circle-alert';
  }

  stateClass(verdict: DipVerdict): string {
    return stateTextClass(fiDipDiagnosis[DIAGNOSIS[verdict]].state);
  }
}
