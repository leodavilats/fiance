import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  CarteiraStore,
  DensityService,
  DialogDirective,
  FiDensity,
  FixedIncomePosition,
  MAX_COMPARE,
  POSITION_COLUMNS,
  PortfolioPosition,
  PositionSortColumn,
  RecommendService,
  RendaFixaTipo,
  SnackbarService,
  UiHelperService,
  parseColumns,
} from '../../core';
import { HelpTooltipComponent } from '../help-tooltip/help-tooltip.component';
import { PageHeaderComponent } from '../page-header/page-header.component';

@Component({
  selector: 'app-positions',
  standalone: true,
  imports: [
    PageHeaderComponent,
    CommonModule,
    DialogDirective,
    FormsModule,
    LucideAngularModule,
    RouterLink,
    HelpTooltipComponent,
  ],
  template: `
    <app-page-header title="Posições" question="O que exatamente eu tenho, linha a linha?" />

    @if (vencimentosProximos().length > 0) {
      <section class="mb-6">
        <div
          class="flex items-start gap-3 p-4 rounded-md border border-attention/40 bg-attention/10"
        >
          <lucide-icon
            name="calendar-clock"
            size="18"
            class="text-attention mt-0.5 shrink-0"
            aria-hidden="true"
          ></lucide-icon>
          <div class="min-w-0">
            <p class="fi-verdict-sm text-ink m-0">
              {{ vencimentosProximos().length === 1 ? 'Uma aplicação vence' : 'Aplicações vencem' }}
              nos próximos 30 dias
            </p>
            <ul class="list-none m-0 p-0 mt-1 flex flex-col gap-0.5">
              @for (v of vencimentosProximos(); track v.id) {
                <li class="fi-caption text-ink-2">
                  <span class="text-ink">{{ v.nome }}</span> — em
                  <span class="fi-num">{{ v.dias_para_vencimento }}</span> dias,
                  <span class="fi-num">{{
                    v.valor_no_vencimento ?? v.valor_atual | currency: 'BRL'
                  }}</span>
                  no vencimento
                </li>
              }
            </ul>
          </div>
        </div>
      </section>
    }

    @if (fixedIncome(); as fi) {
      @if (fixedIncomePositions().length > 0) {
        <section>
          <div class="flex items-baseline justify-between gap-3 flex-wrap mb-1">
            <h2 class="fi-title text-ink m-0">
              Renda fixa
              <span class="text-ink-3 fi-num">({{ fixedIncomePositions().length }})</span>
            </h2>
            <button
              type="button"
              class="btn-quiet"
              [attr.aria-expanded]="showFixedIncomeDetail()"
              (click)="showFixedIncomeDetail.set(!showFixedIncomeDetail())"
            >
              <lucide-icon
                [name]="showFixedIncomeDetail() ? 'chevron-up' : 'chevron-down'"
                size="14"
              ></lucide-icon>
              {{ showFixedIncomeDetail() ? 'Recolher' : 'Detalhar' }}
            </button>
          </div>

          <div class="flex items-baseline gap-8 flex-wrap mt-4">
            <div>
              <p class="fi-eyebrow text-ink-3 m-0">Aplicado</p>
              <p class="fi-metric text-ink m-0">{{ fi.total_investido | currency: 'BRL' }}</p>
            </div>
            <div>
              <p class="fi-eyebrow text-ink-3 m-0">Valor hoje</p>
              <p class="fi-metric text-ink m-0">{{ fi.total_atual | currency: 'BRL' }}</p>
            </div>
            <div>
              <p class="fi-eyebrow text-ink-3 m-0">Rendimento líquido</p>
              <p class="fi-metric text-ink m-0">
                {{ fi.total_rendimento | currency: 'BRL' }}
                <span class="fi-caption text-ink-3">
                  (<span class="fi-num">{{ fi.rendimento_pct | number: '1.2-2' }}</span
                  >%)
                </span>
              </p>
            </div>
          </div>

          <p class="fi-caption text-ink-3 m-0 mt-3">
            Marcado a mercado no servidor, pela mesma regra do comparador. CDI de referência
            <span class="fi-num">{{ fi.cdi_referencia | number: '1.2-2' }}</span
            >% ({{ fi.fonte_taxas === 'bcb' ? 'BCB' : 'estimativa' }}).
          </p>

          @if (showFixedIncomeDetail()) {
            <div class="overflow-x-auto mt-4" [attr.data-density]="density()">
              <table class="w-full border-collapse">
                <caption class="sr-only">
                  Aplicações de renda fixa, com taxa efetiva e valor marcado a mercado
                </caption>
                <thead>
                  <tr class="border-b border-hairline">
                    <th class="text-left py-2 px-2 fi-label text-ink-3">Aplicação</th>
                    <th class="text-left py-2 px-2 fi-label text-ink-3">Tipo</th>
                    <th class="text-right py-2 px-2 fi-label text-ink-3">Rende</th>
                    <th class="text-right py-2 px-2 fi-label text-ink-3">Aplicado</th>
                    <th class="text-right py-2 px-2 fi-label text-ink-3">Hoje</th>
                    <th class="text-right py-2 px-2 fi-label text-ink-3">Rend.</th>
                    <th class="text-right py-2 px-2 fi-label text-ink-3">No vencimento</th>
                    <th class="text-left py-2 px-2 fi-label text-ink-3">Liquidez</th>
                  </tr>
                </thead>
                <tbody>
                  @for (item of fixedIncomePositions(); track trackFixedIncome($index, item)) {
                    <tr
                      class="border-b border-hairline hover:bg-ground-2 transition-colors"
                      [style.height]="'var(--fi-row-height)'"
                    >
                      <td class="px-2 fi-label text-ink">
                        {{ item.nome }}
                        @if (item.isento_ir) {
                          <span class="tag tag-brand ml-1">isento de IR</span>
                        }
                      </td>
                      <td class="px-2 fi-caption text-ink-2">{{ rfTipoLabel(item.tipo) }}</td>
                      <td class="text-right px-2">
                        <span class="fi-num text-ink">{{ rendeLabel(item) }}</span>
                        <span class="fi-caption text-ink-3 block">
                          {{ item.taxa_anual_efetiva_pct | number: '1.2-2' }}% a.a. líquido
                        </span>
                      </td>
                      <td class="text-right px-2 fi-num text-ink">
                        {{ item.valor_investido | number: '1.2-2' }}
                      </td>
                      <td class="text-right px-2 fi-num text-ink">
                        {{ item.valor_atual | number: '1.2-2' }}
                      </td>
                      <td class="text-right px-2 fi-num text-up">
                        +{{ item.rendimento_pct | number: '1.2-2' }}%
                      </td>
                      <td class="text-right px-2 fi-num text-ink-2">
                        {{
                          item.valor_no_vencimento != null
                            ? (item.valor_no_vencimento | number: '1.2-2')
                            : '—'
                        }}
                      </td>
                      <td class="px-2 fi-caption text-ink-2">{{ liquidezLabel(item.liquidez) }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>

            @if (hiddenFixedIncome().length > 0) {
              <p class="fi-caption text-ink-3 mt-3 m-0">
                <span class="fi-num">{{ hiddenFixedIncome().length }}</span> aplicação(ões)
                oculta(s), fora dos totais.
              </p>
            }
          }
        </section>
      }
    }

    @if (tradedPositions().length > 0) {
      <section class="fi-block">
        <div class="flex items-baseline justify-between gap-3 flex-wrap mb-1">
          <h2 class="fi-title text-ink m-0">
            Ativos negociados <span class="text-ink-3 fi-num">({{ negociadosCount() }})</span>
          </h2>
          <a routerLink="/patrimonio/editar" class="btn-link"> Editar carteira </a>
        </div>
        <p class="fi-caption text-ink-3 m-0 mb-4">
          Ações, FIIs, BDRs e ETFs com cotação em bolsa. A leitura compara o preço atual com o preço
          justo estimado.
          <app-help-tooltip term="margem de segurança" [text]="ui.glossary['ms']" />
        </p>

        <div class="flex flex-wrap items-center gap-2 mb-3">
          @if (selectedTickers().length > 0) {
            <span class="fi-caption text-ink-2">
              <span class="fi-num">{{ selectedTickers().length }}/{{ maxCompare }}</span>
              selecionados
            </span>
            <button type="button" class="btn-secondary compact-btn" (click)="compareSelected()">
              <lucide-icon name="git-compare" size="14"></lucide-icon> Comparar
            </button>
            <button type="button" class="btn-secondary compact-btn" (click)="clearSelection()">
              Limpar
            </button>
          }

          <div class="ml-auto flex items-center gap-2">
            <div class="segmented" role="group" aria-label="Densidade da tabela">
              <button
                type="button"
                class="segmented-option"
                [attr.aria-pressed]="density() === 'comfortable'"
                (click)="setDensity('comfortable')"
              >
                Confortável
              </button>
              <button
                type="button"
                class="segmented-option"
                [attr.aria-pressed]="density() === 'compact'"
                (click)="setDensity('compact')"
              >
                Compacta
              </button>
            </div>

            <details class="relative">
              <summary class="btn-secondary compact-btn cursor-pointer list-none">
                <lucide-icon name="table" size="14"></lucide-icon>
                Colunas (<span class="fi-num">{{ visibleColumns().length }}</span
                >)
              </summary>
              <div
                class="absolute right-0 top-full mt-1 z-popover w-[250px] bg-ground-1 border border-hairline rounded-lg shadow-popover p-2"
              >
                @for (col of allColumns; track col.id) {
                  <label
                    class="flex items-start gap-2 px-2 py-1.5 rounded-sm hover:bg-ground-2 cursor-pointer"
                    [class.opacity-60]="col.essential"
                  >
                    <input
                      type="checkbox"
                      class="accent-brand mt-0.5"
                      [checked]="isColumnVisible(col.id)"
                      [disabled]="col.essential"
                      (change)="toggleColumn(col.id)"
                    />
                    <span class="min-w-0">
                      <span class="fi-label text-ink block">{{ col.label }}</span>
                      <span class="fi-caption text-ink-3 block">{{ col.hint }}</span>
                    </span>
                  </label>
                }
              </div>
            </details>

            <button type="button" class="btn-secondary compact-btn" (click)="exportCsv()">
              <lucide-icon name="download" size="14"></lucide-icon> CSV
            </button>
          </div>
        </div>

        <div class="overflow-x-auto" [attr.data-density]="density()">
          <table class="w-full border-collapse">
            <caption class="sr-only">
              Posições negociadas, com preço médio, cotação atual e leitura do sistema
            </caption>
            <!-- design-exception: camada — o cabecalho grudado precisa cobrir so as celulas da propria tabela -->
            <thead>
              <tr class="border-b border-hairline">
                <th class="py-2 px-2 w-8"><span class="sr-only">Selecionar para comparar</span></th>
                @for (col of columns(); track col.id) {
                  <th
                    class="py-2 px-2 fi-label text-ink-3 sticky top-0 bg-ground z-10"
                    [class.text-left]="col.align === 'left'"
                    [class.text-right]="col.align === 'right'"
                    [attr.aria-sort]="ariaSort(col.id)"
                  >
                    @if (col.sortable) {
                      <button
                        type="button"
                        class="th-sort"
                        [class.justify-end]="col.align === 'right'"
                        [attr.aria-label]="'Ordenar por ' + col.label"
                        (click)="toggleSort(sortableId(col.id))"
                      >
                        {{ col.label }}
                        <lucide-icon [name]="sortIcon(sortableId(col.id))" size="12"></lucide-icon>
                      </button>
                    } @else {
                      {{ col.label }}
                    }
                  </th>
                }
                <th class="text-right py-2 px-2 w-[88px]"><span class="sr-only">Ações</span></th>
              </tr>
            </thead>
            <tbody>
              @for (p of tradedPositions(); track p.ticker) {
                <tr
                  class="border-b border-hairline hover:bg-ground-2 transition-colors"
                  [class.row-highlight]="isSelected(p.ticker)"
                  [style.height]="'var(--fi-row-height)'"
                >
                  <td class="px-2">
                    <input
                      type="checkbox"
                      class="accent-brand cursor-pointer"
                      [checked]="isSelected(p.ticker)"
                      (change)="toggleSelection(p.ticker)"
                      [attr.aria-label]="'Selecionar ' + p.ticker + ' para comparar'"
                    />
                  </td>

                  @for (col of columns(); track col.id) {
                    <td
                      class="px-2"
                      [class.text-left]="col.align === 'left'"
                      [class.text-right]="col.align === 'right'"
                    >
                      @switch (col.id) {
                        @case ('ticker') {
                          <a
                            [routerLink]="['/ativo', p.ticker]"
                            class="fi-ticker text-ink no-underline hover:text-brand transition-colors"
                            >{{ p.ticker }}</a
                          >
                          @if (p.name && density() === 'comfortable') {
                            <span class="fi-caption text-ink-3 block truncate max-w-[180px]">{{
                              p.name
                            }}</span>
                          }
                        }
                        @case ('asset_type') {
                          <span class="tag" [class]="ui.categoryChipClass(p.category_resolved)">{{
                            ui.assetTypeLabel(p.asset_type)
                          }}</span>
                        }
                        @case ('quantity') {
                          <span class="fi-num text-ink">{{ p.quantity }}</span>
                        }
                        @case ('avg_price') {
                          <span class="fi-num text-ink">{{ p.avg_price | number: '1.2-2' }}</span>
                        }
                        @case ('current_price') {
                          <span class="fi-num text-ink">{{ dash(p.current_price) }}</span>
                        }
                        @case ('current_value') {
                          <span class="fi-num text-ink">{{ dash(p.current_value) }}</span>
                        }
                        @case ('weight') {
                          <span class="fi-num text-ink-2">{{ weightLabel(p) }}</span>
                        }
                        @case ('fair_price') {
                          <span class="fi-num text-ink">{{ dash(p.fair_price) }}</span>
                        }
                        @case ('margin') {
                          @if (p.margin_of_safety != null) {
                            <span
                              class="fi-num"
                              [class.text-favorable]="p.margin_of_safety > 0"
                              [class.text-attention]="p.margin_of_safety <= 0"
                            >
                              {{ p.margin_of_safety * 100 | number: '1.0-0' }}%
                            </span>
                          } @else {
                            <span class="text-indeterminate">—</span>
                          }
                        }
                        @case ('pnl_pct') {
                          <span
                            class="fi-num"
                            [class.text-up]="(p.pnl_pct || 0) >= 0"
                            [class.text-down]="(p.pnl_pct || 0) < 0"
                          >
                            {{ p.pnl_pct != null ? (p.pnl_pct | number: '1.2-2') + '%' : '—' }}
                          </span>
                        }
                        @case ('verdict') {
                          <button
                            type="button"
                            class="verdict-pill cursor-pointer border-0"
                            [class]="ui.verdictClass(p.verdict)"
                            [attr.aria-expanded]="expandedReasonsTicker() === p.ticker"
                            [title]="p.reasons.length ? 'Ver motivos' : ''"
                            (click)="toggleReasons(p.ticker)"
                          >
                            {{ p.label }}
                            @if (p.reasons.length) {
                              <lucide-icon
                                [name]="
                                  expandedReasonsTicker() === p.ticker
                                    ? 'chevron-up'
                                    : 'chevron-down'
                                "
                                size="12"
                              ></lucide-icon>
                            }
                          </button>
                          @if (density() === 'comfortable') {
                            <span class="fi-caption text-ink-3 block">
                              {{ ui.dataYearsLabel(p.data_years) }} ·
                              {{ ui.consensusLabel(p.consensus_methods) }}
                            </span>
                          }
                        }
                      }
                    </td>
                  }

                  <td class="text-right px-2">
                    <button
                      type="button"
                      class="btn-secondary compact-btn"
                      (click)="openSellModal(p)"
                    >
                      Vender
                    </button>
                  </td>
                </tr>

                @if (expandedReasonsTicker() === p.ticker && p.reasons.length) {
                  <tr class="border-b border-hairline bg-ground-2">
                    <td [attr.colspan]="columns().length + 2" class="py-2 px-4">
                      <ul class="list-disc pl-4 fi-caption text-ink-2 leading-relaxed m-0">
                        @for (reason of p.reasons; track reason) {
                          <li>{{ reason }}</li>
                        }
                      </ul>
                    </td>
                  </tr>
                }
              }
            </tbody>
          </table>
        </div>
      </section>
    }

    @if (sellModal(); as modal) {
      <div
        class="fixed inset-0 z-popover fi-overlay flex items-center justify-center p-4"
        (click)="closeSellModal()"
      >
        <div
          fiDialog
          class="relative w-full max-w-sm rounded-lg border border-hairline bg-ground-1 shadow-popover p-5"
          role="dialog"
          aria-modal="true"
          [attr.aria-label]="'Vender ' + modal.position.ticker"
          (click)="$event.stopPropagation()"
        >
          <h2 class="fi-title text-ink m-0 mb-1">Vender {{ modal.position.ticker }}</h2>
          <p class="fi-caption text-ink-3 m-0 mb-4">
            Lucro, imposto de renda e prejuízo a compensar são calculados no servidor a partir do
            que você informar aqui.
          </p>

          <div class="flex flex-col gap-3">
            <label class="flex flex-col gap-1 fi-label text-ink-2">
              Quantidade (máx. <span class="fi-num">{{ modal.position.quantity }}</span
              >)
              <input
                type="number"
                class="input"
                [ngModel]="modal.quantity"
                (ngModelChange)="updateSellQuantity($event)"
                [max]="modal.position.quantity"
                min="0"
              />
            </label>
            <label class="flex flex-col gap-1 fi-label text-ink-2">
              Preço de venda (R$)
              <input
                type="number"
                class="input"
                [ngModel]="modal.price"
                (ngModelChange)="updateSellPrice($event)"
                min="0"
                step="0.01"
              />
            </label>
          </div>

          <div class="flex items-center justify-end gap-3 mt-5">
            <button
              type="button"
              class="btn-secondary"
              (click)="closeSellModal()"
              [disabled]="sellingInProgress()"
              [title]="sellingInProgress() ? 'A venda já está sendo registrada' : ''"
            >
              Cancelar
            </button>
            <button
              type="button"
              class="btn-primary"
              (click)="confirmSell()"
              [disabled]="sellingInProgress()"
            >
              {{ sellingInProgress() ? 'Registrando…' : 'Confirmar venda' }}
            </button>
          </div>
        </div>
      </div>
    }
  `,
})
export class PositionsComponent implements OnInit {
  private readonly densidade = inject(DensityService);
  private readonly store = inject(CarteiraStore);
  private readonly svc = inject(RecommendService);
  private readonly snackbar = inject(SnackbarService);
  private readonly router = inject(Router);
  readonly ui = inject(UiHelperService);

  readonly tradedPositions = this.store.tradedPositions;
  readonly fixedIncome = this.store.fixedIncome;
  readonly fixedIncomePositions = this.store.fixedIncomePositions;
  readonly hiddenFixedIncome = this.store.hiddenFixedIncome;
  readonly vencimentosProximos = this.store.vencimentosProximos;
  readonly negociadosCount = this.store.negociadosCount;
  readonly selectedTickers = this.store.selectedTickers;

  readonly maxCompare = MAX_COMPARE;

  readonly allColumns = POSITION_COLUMNS;
  readonly visibleColumns = signal<string[]>([]);
  readonly density = signal<FiDensity>('comfortable');

  readonly columns = computed(() =>
    POSITION_COLUMNS.filter(c => this.visibleColumns().includes(c.id as string))
  );

  readonly showFixedIncomeDetail = signal(true);
  readonly expandedReasonsTicker = signal<string | null>(null);
  readonly sellModal = signal<{
    position: PortfolioPosition;
    quantity: number;
    price: number;
  } | null>(null);
  readonly sellingInProgress = signal(false);

  private readonly route = inject(ActivatedRoute);

  ngOnInit(): void {
    this.store.ensureLoaded();

    const q = this.route.snapshot.queryParamMap;
    this.visibleColumns.set(parseColumns(q.get('cols')));

    const daUrl = q.get('d');
    this.density.set(
      daUrl === 'compact' || daUrl === 'comfortable' ? daUrl : this.densidade.density()
    );
  }

  private syncUrl(): void {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        cols: this.visibleColumns().join(','),
        d: this.density() === 'compact' ? 'compact' : null,
      },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  setDensity(density: FiDensity): void {
    this.density.set(density);
    this.syncUrl();
  }

  isColumnVisible(id: string): boolean {
    return this.visibleColumns().includes(id);
  }

  toggleColumn(id: string): void {
    const column = POSITION_COLUMNS.find(c => c.id === id);
    if (!column || column.essential) return;
    const next = this.isColumnVisible(id)
      ? this.visibleColumns().filter(c => c !== id)
      : [...this.visibleColumns(), id];
    this.visibleColumns.set(parseColumns(next.join(',')));
    this.syncUrl();
  }

  sortableId(id: string): PositionSortColumn {
    if (id === 'weight') return 'current_value';
    if (id === 'margin') return 'fair_price';
    return id as PositionSortColumn;
  }

  ariaSort(id: string): 'ascending' | 'descending' | 'none' {
    if (this.store.sortColumn() !== this.sortableId(id)) return 'none';
    return this.store.sortDirection() === 'asc' ? 'ascending' : 'descending';
  }

  dash(value: number | null | undefined): string {
    return value == null
      ? '—'
      : value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  weightLabel(p: PortfolioPosition): string {
    const total = this.tradedPositions().reduce((sum, x) => sum + (x.current_value ?? 0), 0);
    if (total <= 0 || p.current_value == null) return '—';
    return `${((p.current_value / total) * 100).toFixed(1)}%`;
  }

  rendeLabel(item: FixedIncomePosition): string {
    const pct = item.pct_cdi_equivalente;
    if (pct != null) return `~${pct.toFixed(0)}% do CDI`;
    return `${item.taxa_anual_efetiva_pct.toFixed(2)}% a.a.`;
  }

  toggleSort(column: PositionSortColumn): void {
    this.store.toggleSort(column);
  }

  sortIcon(column: PositionSortColumn): string {
    return this.store.sortIcon(column);
  }

  isSelected(ticker: string): boolean {
    return this.store.isSelected(ticker);
  }

  toggleSelection(ticker: string): void {
    this.store.toggleSelection(ticker);
  }

  clearSelection(): void {
    this.store.clearSelection();
  }

  compareSelected(): void {
    const tickers = this.selectedTickers();
    if (tickers.length < 2) {
      this.snackbar.showError('Selecione ao menos dois ativos para comparar.');
      return;
    }
    this.router.navigate(['/descobrir/comparar'], {
      queryParams: { tickers: tickers.join(',') },
    });
  }

  toggleReasons(ticker: string): void {
    this.expandedReasonsTicker.set(this.expandedReasonsTicker() === ticker ? null : ticker);
  }

  rfTipoLabel(tipo: RendaFixaTipo | string): string {
    return this.ui.fixedIncomeTypeLabel(tipo);
  }

  liquidezLabel(liquidez: string): string {
    return this.ui.liquidityLabel(liquidez);
  }

  trackFixedIncome(_: number, item: FixedIncomePosition): number {
    return item.id;
  }

  exportCsv(): void {
    const rows: string[][] = [
      [
        'Ativo',
        'Nome',
        'Tipo',
        'Quantidade',
        'Preco medio',
        'Preco atual',
        'Preco justo',
        'Investido',
        'Valor atual',
        'Rendimento %',
        'Veredito',
        'Setor',
      ],
    ];

    for (const p of this.tradedPositions()) {
      rows.push([
        p.ticker,
        p.name ?? '',
        this.ui.assetTypeLabel(p.asset_type),
        this.num(p.quantity),
        this.num(p.avg_price),
        this.num(p.current_price),
        this.num(p.fair_price),
        this.num(p.invested),
        this.num(p.current_value),
        this.num(p.pnl_pct),
        p.label,
        p.sector ? this.ui.translateSector(p.sector) : '',
      ]);
    }

    for (const item of this.fixedIncomePositions()) {
      rows.push([
        item.nome,
        item.tipo + ' · ' + item.taxa_anual_efetiva_pct.toFixed(2) + '% a.a.',
        'Renda Fixa',
        '1',
        this.num(item.valor_investido),
        this.num(item.valor_atual),
        '',
        this.num(item.valor_investido),
        this.num(item.valor_atual),
        this.num(item.rendimento_pct),
        'Manter',
        'Renda Fixa',
      ]);
    }

    const csv = rows
      .map(row => row.map(cell => '"' + cell.replace(/"/g, '""') + '"').join(';'))
      .join('\r\n');

    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'carteira-' + new Date().toISOString().slice(0, 10) + '.csv';
    link.click();
    URL.revokeObjectURL(url);
  }

  private num(value: number | null | undefined): string {
    if (value == null) return '';
    return value.toFixed(2).replace('.', ',');
  }

  openSellModal(p: PortfolioPosition): void {
    this.sellModal.set({
      position: p,
      quantity: p.quantity,
      price: p.current_price ?? p.avg_price,
    });
  }

  closeSellModal(): void {
    if (this.sellingInProgress()) return;
    this.sellModal.set(null);
  }

  updateSellQuantity(quantity: number): void {
    const modal = this.sellModal();
    if (modal) this.sellModal.set({ ...modal, quantity });
  }

  updateSellPrice(price: number): void {
    const modal = this.sellModal();
    if (modal) this.sellModal.set({ ...modal, price });
  }

  confirmSell(): void {
    const modal = this.sellModal();
    if (!modal) return;

    const { position, quantity, price } = modal;
    if (quantity <= 0 || quantity > position.quantity || price <= 0) {
      this.snackbar.showError('Quantidade ou preço de venda inválidos.');
      return;
    }

    this.sellingInProgress.set(true);
    this.svc.sellPosition({ ticker: position.ticker, quantity, sell_price: price }).subscribe({
      next: trade => {
        this.sellingInProgress.set(false);
        this.sellModal.set(null);
        const lucro = trade.net_profit >= 0 ? 'lucro' : 'prejuízo';
        const ir = trade.ir_amount > 0 ? ' (IR: R$ ' + trade.ir_amount.toFixed(2) + ')' : '';
        this.snackbar.showSuccess(
          'Venda registrada: ' +
            lucro +
            ' líquido de R$ ' +
            Math.abs(trade.net_profit).toFixed(2) +
            ir
        );
        this.store.loadClosedTrades();
        this.store.reloadPositions();
      },
      error: err => {
        this.sellingInProgress.set(false);
        this.snackbar.showError(err?.error?.detail || 'Erro ao registrar venda.');
      },
    });
  }
}
