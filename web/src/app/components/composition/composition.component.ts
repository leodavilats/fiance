import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CarteiraStore, UiHelperService, allocationScalePct } from '../../core';
import { AllocationGapComponent } from '../allocation-gap/allocation-gap.component';
import { EmptyStateComponent } from '../empty-state/empty-state.component';
import { SkeletonComponent } from '../skeleton/skeleton.component';

@Component({
  selector: 'app-composition',
  standalone: true,
  imports: [
    AllocationGapComponent,
    CommonModule,
    EmptyStateComponent,
    RouterLink,
    SkeletonComponent,
  ],
  template: `
    @if (isEmpty()) {
      <app-empty-state
        icon="chart-pie"
        title="Nenhuma posição para compor"
        reason="A composição mostra como o seu dinheiro está distribuído — e ainda não há posição cadastrada para distribuir."
        nextStep="Cadastre o que você já tem; a composição, a saúde e a estratégia passam a existir a partir disso."
        actionLabel="Cadastrar carteira"
        actionRoute="/patrimonio/editar"
      />
    } @else {
      <div class="max-w-reading">
        <section>
          <h1 class="fi-page-title text-ink m-0">Onde meu dinheiro está concentrado</h1>
          <p class="fi-body text-ink-2 m-0 mt-1">
            A barra é o peso de cada posição no total. Quando existe meta para a classe, o fio marca
            onde ela deveria estar.
          </p>

          @if (alocacaoPorTipo().length === 0) {
            <div class="mt-6 flex flex-col gap-4">
              <app-skeleton shape="title" />
              <app-skeleton shape="row" [count]="5" />
            </div>
          } @else {
            <div
              class="flex items-center gap-1 mt-4"
              role="group"
              aria-label="Recorte da composição"
            >
              <button
                type="button"
                class="subtab-btn"
                [class.active]="composicaoMode() === 'ativo'"
                [attr.aria-pressed]="composicaoMode() === 'ativo'"
                (click)="setComposicaoMode('ativo')"
              >
                Por classe
              </button>
              <button
                type="button"
                class="subtab-btn"
                [class.active]="composicaoMode() === 'setor'"
                [attr.aria-pressed]="composicaoMode() === 'setor'"
                (click)="setComposicaoMode('setor')"
              >
                Por setor (ações e BDRs)
              </button>
            </div>

            @if (composicaoMode() === 'setor' && alocacaoPorSetor().length === 0) {
              <div class="mt-4">
                <app-empty-state
                  icon="chart-bar"
                  title="Sem ações ou BDRs para recortar por setor"
                  reason="A visão por setor cobre apenas ações e BDRs — a carteira atual não tem nenhum desses."
                  nextStep="A visão por classe continua respondendo onde o dinheiro está."
                  actionLabel="Ver por classe"
                  (action)="setComposicaoMode('ativo')"
                />
              </div>
            } @else {
              <ul class="list-none m-0 p-0 mt-6 flex flex-col gap-4">
                @for (s of composicaoSlices(); track s.label) {
                  <li>
                    <app-allocation-gap
                      [label]="s.label"
                      [currentPct]="s.pct"
                      [targetPct]="targetFor(s.label)"
                      [barColor]="s.color"
                      [scalePct]="gapScalePct()"
                    />
                    <p class="fi-caption text-ink-3 m-0 mt-1 ml-[104px] sm:ml-[116px] fi-num">
                      {{ s.valor | currency: 'BRL' }}
                    </p>
                  </li>
                }
              </ul>

              @if (!hasAnyTarget()) {
                <p class="fi-caption text-ink-3 m-0 mt-5 pt-4 border-t border-hairline">
                  Nenhuma meta definida para estas classes — sem meta, a composição diz onde o
                  dinheiro está, mas não se está certo.
                  <a routerLink="/voce/objetivos" class="text-brand">Definir metas →</a>
                </p>
              }
            }
          }
        </section>
      </div>
    }
  `,
})
export class CompositionComponent implements OnInit {
  private readonly store = inject(CarteiraStore);
  readonly ui = inject(UiHelperService);

  readonly isEmpty = this.store.isEmpty;
  readonly composicaoMode = this.store.composicaoMode;
  readonly composicaoSlices = this.store.composicaoSlices;
  readonly alocacaoPorTipo = this.store.alocacaoPorTipo;
  readonly alocacaoPorSetor = this.store.alocacaoPorSetor;

  ngOnInit(): void {
    this.store.ensureLoaded();
  }

  setComposicaoMode(mode: 'ativo' | 'setor'): void {
    this.store.composicaoMode.set(mode);
  }

  targetFor(label: string): number | null {
    return this.composicaoSlices().find(s => s.label === label)?.targetPct ?? null;
  }

  readonly gapScalePct = computed(() =>
    allocationScalePct(
      this.composicaoSlices().map(s => ({ currentPct: s.pct, targetPct: s.targetPct ?? null }))
    )
  );

  readonly hasAnyTarget = computed(() => this.composicaoSlices().some(s => s.targetPct != null));
}
