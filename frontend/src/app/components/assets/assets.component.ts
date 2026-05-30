import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormControl,
  FormArray,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import {
  AllocationCategory,
  LoadingService,
  PortfolioItem,
  PortfolioEvaluationResponse,
  RecommendService,
  RendaFixaTipo,
  UiHelperService,
} from '../../core';

interface PortfolioItemForm {
  ticker: FormControl<string>;
  quantity: FormControl<number>;
  avg_price: FormControl<number>;
  category: FormControl<'auto' | 'renda' | 'trade'>;
}

interface RendaFixaItemForm {
  nome: FormControl<string>;
  tipo: FormControl<RendaFixaTipo>;
  valor_investido: FormControl<number>;
  taxa: FormControl<number>;
  prazo_meses: FormControl<number>;
  data_aplicacao: FormControl<string>;
  tipo_taxa: FormControl<'pre_fixado' | 'pos_fixado' | 'hibrido'>;
  percentual_cdi: FormControl<number | null>;
}

interface PortfolioFormShape {
  items: FormArray<FormGroup<PortfolioItemForm>>;
  renda_fixa: FormArray<FormGroup<RendaFixaItemForm>>;
  desired_yield: FormControl<number>;
}

@Component({
  selector: 'app-assets',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  template: `
    <!-- Ativos Negociados -->
    <div class="p-5 rounded-lg bg-panel border border-border mb-5">
      <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-3 text-tx">
        <lucide-icon name="trending-up" size="18"></lucide-icon> Ativos Negociados
      </h2>
      <p class="text-sm text-muted mb-4">
        Ações, FIIs, criptomoedas e outros ativos com ticker/cotação em bolsa.
      </p>

      <form [formGroup]="form">
        <div
          class="grid grid-cols-[2fr_1fr_1fr_1.5fr_auto] gap-2 mb-2 text-sm font-medium text-muted"
        >
          <div>Ticker</div>
          <div>Quantidade</div>
          <div>Preço médio</div>
          <div>Categoria</div>
          <div></div>
        </div>
        <div class="flex flex-col gap-2" formArrayName="items">
          @for (item of portfolioItems.controls; track $index; let i = $index) {
            <div
              class="grid grid-cols-[2fr_1fr_1fr_1.5fr_auto] gap-2 items-center"
              [formGroupName]="i"
            >
              <input
                type="text"
                formControlName="ticker"
                placeholder="ex.: PETR4"
                class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <input
                type="number"
                formControlName="quantity"
                placeholder="qtd"
                step="0.0001"
                min="0"
                class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <input
                type="number"
                formControlName="avg_price"
                placeholder="preço"
                step="0.01"
                min="0"
                class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <select
                formControlName="category"
                class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent cursor-pointer"
              >
                <option value="auto">Auto</option>
                <option value="renda">Renda</option>
                <option value="trade">Trade</option>
              </select>
              <button
                type="button"
                class="w-9 h-9 grid place-items-center rounded-lg cursor-pointer bg-panel-2 border border-border text-danger hover:bg-danger hover:text-white transition-colors"
                (click)="removeItem(i)"
                title="Remover"
              >
                <lucide-icon name="x" size="16"></lucide-icon>
              </button>
            </div>
          }
        </div>
        <div class="flex items-center gap-3 mt-4 flex-wrap">
          <button
            type="button"
            class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all"
            (click)="addItem()"
          >
            <lucide-icon name="plus" size="16"></lucide-icon> Adicionar ativo
          </button>
          <button
            type="button"
            class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-accent text-white border-0 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
            (click)="evaluateAssets()"
            [disabled]="loading.loading() || portfolioItems.length === 0"
          >
            <lucide-icon
              [name]="loading.loading() ? 'loader-circle' : 'refresh-cw'"
              size="16"
            ></lucide-icon>
            {{ loading.loading() ? 'Avaliando...' : 'Avaliar agora' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Renda Fixa -->
    <div class="p-5 rounded-lg bg-panel border border-border mb-5">
      <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-3 text-tx">
        <lucide-icon name="landmark" size="18"></lucide-icon> Renda Fixa
      </h2>
      <p class="text-sm text-muted mb-4">
        CDB, LCI, LCA, Tesouro Direto e outros títulos de renda fixa.
      </p>

      <form [formGroup]="form">
        <div
          class="grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_1fr_1.2fr_auto] gap-2 mb-2 text-sm font-medium text-muted"
        >
          <div>Nome/Banco</div>
          <div>Tipo</div>
          <div>Tipo Taxa</div>
          <div>Valor (R$)</div>
          <div>Taxa/% CDI</div>
          <div>Prazo (m)</div>
          <div>Aplicação</div>
          <div></div>
        </div>
        <div class="flex flex-col gap-2" formArrayName="renda_fixa">
          @for (rf of rendaFixaItems.controls; track $index; let i = $index) {
            <div
              class="grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_1fr_1.2fr_auto] gap-2 items-start"
              [formGroupName]="i"
            >
              <input
                type="text"
                formControlName="nome"
                placeholder="ex.: Banco Inter"
                class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <select
                formControlName="tipo"
                class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent cursor-pointer"
              >
                <option value="cdb">CDB</option>
                <option value="lci">LCI</option>
                <option value="lca">LCA</option>
                <option value="tesouro_selic">Tesouro Selic</option>
                <option value="tesouro_ipca">Tesouro IPCA+</option>
                <option value="tesouro_pre">Tesouro Pré</option>
                <option value="lc">LC</option>
                <option value="cri">CRI</option>
                <option value="cra">CRA</option>
              </select>
              <select
                formControlName="tipo_taxa"
                class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent cursor-pointer"
              >
                <option value="pre_fixado">Pré</option>
                <option value="pos_fixado">Pós (CDI)</option>
                <option value="hibrido">Híbrido</option>
              </select>
              <input
                type="number"
                formControlName="valor_investido"
                placeholder="10000"
                min="0"
                step="100"
                class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              />
              @if (rf.controls.tipo_taxa.value === 'pos_fixado') {
                <input
                  type="number"
                  formControlName="percentual_cdi"
                  placeholder="110"
                  min="0"
                  step="1"
                  class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                />
              } @else {
                <input
                  type="number"
                  formControlName="taxa"
                  placeholder="12.5"
                  min="0"
                  step="0.1"
                  class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                />
              }
              <input
                type="number"
                formControlName="prazo_meses"
                placeholder="12"
                min="1"
                step="1"
                class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <input
                type="date"
                formControlName="data_aplicacao"
                class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <button
                type="button"
                class="w-9 h-9 grid place-items-center rounded-lg cursor-pointer bg-panel-2 border border-border text-danger hover:bg-danger hover:text-white transition-colors"
                (click)="removeRF(i)"
                title="Remover"
              >
                <lucide-icon name="x" size="16"></lucide-icon>
              </button>
            </div>
          }
        </div>
        @if (rendaFixaItems.length === 0) {
          <div class="text-center py-6 text-muted text-sm">
            Nenhum ativo de renda fixa cadastrado. Clique em "Adicionar RF" para começar.
          </div>
        }
        <div class="flex items-center gap-3 mt-4 flex-wrap">
          <button
            type="button"
            class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all"
            (click)="addRF()"
          >
            <lucide-icon name="plus" size="16"></lucide-icon> Adicionar RF
          </button>
        </div>
      </form>
    </div>

    <!-- Resumo Renda Fixa -->
    @if (rendaFixaItems.length > 0) {
      <div class="p-5 rounded-lg bg-panel border border-border mb-5">
        <h2 class="text-xl font-bold m-0 mb-4 text-tx">Renda Fixa - Resumo</h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
          <div class="p-4 rounded-lg bg-bg-2 border border-border">
            <div class="text-xs text-muted mb-1">Total Investido</div>
            <div class="text-xl font-bold text-tx">R$ {{ totalRendaFixa() | number: '1.2-2' }}</div>
          </div>
          <div class="p-4 rounded-lg bg-bg-2 border border-border">
            <div class="text-xs text-muted mb-1">Quantidade</div>
            <div class="text-xl font-bold text-tx">{{ rendaFixaItems.length }}</div>
          </div>
          <div class="p-4 rounded-lg bg-bg-2 border border-border">
            <div class="text-xs text-muted mb-1">Taxa Média</div>
            <div class="text-xl font-bold text-tx">{{ avgTaxaRF() | number: '1.2-2' }}% a.a.</div>
          </div>
        </div>
        <div style="overflow-x:auto;">
          <table class="w-full border-collapse text-sm">
            <thead>
              <tr class="border-b border-border">
                <th class="text-left py-2 px-2 font-medium text-muted">Nome</th>
                <th class="text-left py-2 px-2 font-medium text-muted">Tipo</th>
                <th class="text-right py-2 px-2 font-medium text-muted">Valor</th>
                <th class="text-right py-2 px-2 font-medium text-muted">Taxa</th>
                <th class="text-right py-2 px-2 font-medium text-muted">Prazo</th>
                <th class="text-left py-2 px-2 font-medium text-muted">Aplicação</th>
              </tr>
            </thead>
            <tbody>
              @for (rf of rendaFixaItems.controls; track $index) {
                <tr class="border-b border-border hover:bg-bg-2 transition-colors">
                  <td class="py-2 px-2 text-tx font-medium">{{ rf.controls.nome.value }}</td>
                  <td class="py-2 px-2">
                    <span class="tag">{{ rfTipoLabel(rf.controls.tipo.value) }}</span>
                  </td>
                  <td class="text-right py-2 px-2 text-tx">
                    R$ {{ rf.controls.valor_investido.value | number: '1.2-2' }}
                  </td>
                  <td class="text-right py-2 px-2 text-tx">
                    @if (rf.controls.tipo_taxa.value === 'pos_fixado') {
                      {{ rf.controls.percentual_cdi.value }}% CDI
                    } @else {
                      {{ rf.controls.taxa.value }}% a.a.
                    }
                  </td>
                  <td class="text-right py-2 px-2 text-tx">{{ rf.controls.prazo_meses.value }}m</td>
                  <td class="py-2 px-2 text-muted">
                    {{ rf.controls.data_aplicacao.value | date: 'dd/MM/yyyy' }}
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    }

    @if (result(); as r) {
      <div class="p-5 rounded-lg bg-panel border border-border">
        <h2 class="text-xl font-bold m-0 mb-3 text-tx">Resumo</h2>
        <p class="leading-relaxed text-sm text-tx">
          {{ ui.portfolioSummary(r.positions, r.total_pnl, r.total_pnl_pct) }}
        </p>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
          <div class="p-4 rounded-lg bg-bg-2 border border-border info">
            <div class="text-xs text-muted mb-1">Investido</div>
            <div class="text-xl font-bold text-tx">R$ {{ r.total_invested | number: '1.2-2' }}</div>
          </div>
          <div
            class="p-4 rounded-lg bg-bg-2 border border-border"
            [class.good]="r.total_pnl >= 0"
            [class.warn]="r.total_pnl < 0"
          >
            <div class="text-xs text-muted mb-1">Valor atual</div>
            <div class="text-xl font-bold text-tx">R$ {{ r.total_current | number: '1.2-2' }}</div>
          </div>
          <div
            class="p-4 rounded-lg bg-bg-2 border border-border"
            [class.good]="r.total_pnl >= 0"
            [class.warn]="r.total_pnl < 0"
          >
            <div class="text-xs text-muted mb-1">Resultado</div>
            <div class="text-xl font-bold text-tx">
              {{ r.total_pnl >= 0 ? '+' : '' }}R$ {{ r.total_pnl | number: '1.2-2' }} ({{
                r.total_pnl_pct | number: '1.2-2'
              }}%)
            </div>
          </div>
        </div>
      </div>

      <div class="p-5 rounded-lg bg-panel border border-border">
        <h2 class="text-xl font-bold m-0 mb-4 text-tx">Posições</h2>
        <div style="overflow-x:auto;">
          <table class="w-full border-collapse text-sm">
            <thead>
              <tr class="border-b border-border">
                <th class="text-left py-2 px-2 font-medium text-muted">Ativo</th>
                <th class="text-left py-2 px-2 font-medium text-muted">Categoria</th>
                <th class="text-right py-2 px-2 font-medium text-muted">Qtd</th>
                <th class="text-right py-2 px-2 font-medium text-muted">P. médio</th>
                <th class="text-right py-2 px-2 font-medium text-muted">P. atual</th>
                <th class="text-right py-2 px-2 font-medium text-muted">P. justo</th>
                <th class="text-right py-2 px-2 font-medium text-muted">PnL</th>
                <th class="text-left py-2 px-2 font-medium text-muted">Decisão</th>
              </tr>
            </thead>
            <tbody>
              @for (p of r.positions; track p.ticker) {
                <tr class="border-b border-border hover:bg-bg-2 transition-colors">
                  <td class="py-2 px-2">
                    <div class="font-semibold text-tx">{{ p.ticker }}</div>
                    <div class="text-xs text-muted">{{ p.name }}</div>
                  </td>
                  <td class="py-2 px-2">
                    <span class="tag tag-cat" [class]="'cat-' + p.category_resolved">{{
                      ui.categoryLabel(p.category_resolved)
                    }}</span>
                  </td>
                  <td class="text-right py-2 px-2 text-tx">{{ p.quantity }}</td>
                  <td class="text-right py-2 px-2 text-tx">{{ p.avg_price | number: '1.2-2' }}</td>
                  <td class="text-right py-2 px-2 text-tx">
                    {{ p.current_price != null ? (p.current_price | number: '1.2-2') : '—' }}
                  </td>
                  <td class="text-right py-2 px-2 text-tx">
                    {{ p.fair_price != null ? (p.fair_price | number: '1.2-2') : '—' }}
                  </td>
                  <td
                    class="text-right py-2 px-2"
                    [class.good]="(p.pnl_pct || 0) >= 0"
                    [class.warn]="(p.pnl_pct || 0) < 0"
                  >
                    {{ p.pnl_pct != null ? (p.pnl_pct | number: '1.2-2') + '%' : '—' }}
                  </td>
                  <td class="py-2 px-2">
                    <span class="verdict-pill" [class]="ui.verdictClass(p.verdict)">{{
                      p.label
                    }}</span>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    }
  `,
  styles: [
    `
      .tag {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        font-weight: 500;
        background-color: rgb(var(--cat-renda_fixa) / 0.15);
        color: rgb(var(--cat-renda_fixa));
      }
    `,
  ],
})
export class AssetsComponent implements OnInit {
  private fb = inject(FormBuilder);
  private svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  result = signal<PortfolioEvaluationResponse | null>(null);
  saveState = signal<'idle' | 'saving' | 'saved' | 'error'>('idle');

  private save$ = new Subject<void>();

  form: FormGroup<PortfolioFormShape> = this.fb.group({
    items: this.fb.array<FormGroup<PortfolioItemForm>>([]),
    renda_fixa: this.fb.array<FormGroup<RendaFixaItemForm>>([]),
    desired_yield: this.fb.control(0.06, {
      nonNullable: true,
      validators: [Validators.min(0.02), Validators.max(0.2)],
    }),
  });

  get portfolioItems() {
    return this.form.controls.items;
  }

  get rendaFixaItems() {
    return this.form.controls.renda_fixa;
  }

  ngOnInit(): void {
    this.loadStoredPortfolio();
    this.loadStoredRendaFixa();

    this.form.valueChanges.subscribe(() => {
      this.save$.next();
    });

    this.save$.pipe(debounceTime(800)).subscribe(() => {
      this.persistPortfolio();
      this.persistRendaFixa();
    });
  }

  addItem(): void {
    const group = this.fb.group<PortfolioItemForm>({
      ticker: this.fb.control('', { nonNullable: true, validators: Validators.required }),
      quantity: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(0.0001)],
      }),
      avg_price: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(0.0001)],
      }),
      category: this.fb.control<'auto' | 'renda' | 'trade'>('auto', { nonNullable: true }),
    });
    this.portfolioItems.push(group);
  }

  removeItem(i: number): void {
    this.portfolioItems.removeAt(i);
  }

  addRF(): void {
    const group = this.fb.group<RendaFixaItemForm>({
      nome: this.fb.control('', { nonNullable: true, validators: Validators.required }),
      tipo: this.fb.control<RendaFixaTipo>('cdb', { nonNullable: true }),
      valor_investido: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(1)],
      }),
      taxa: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(0)],
      }),
      prazo_meses: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(1)],
      }),
      data_aplicacao: this.fb.control('', { nonNullable: true, validators: Validators.required }),
      tipo_taxa: this.fb.control<'pre_fixado' | 'pos_fixado' | 'hibrido'>('pre_fixado', {
        nonNullable: true,
      }),
      percentual_cdi: this.fb.control<number | null>(null),
    });
    this.rendaFixaItems.push(group);
  }

  removeRF(i: number): void {
    this.rendaFixaItems.removeAt(i);
  }

  totalRendaFixa(): number {
    return this.rendaFixaItems.controls.reduce(
      (sum, rf) => sum + (rf.controls.valor_investido.value || 0),
      0
    );
  }

  avgTaxaRF(): number {
    if (this.rendaFixaItems.length === 0) return 0;
    const total = this.totalRendaFixa();
    if (total === 0) return 0;

    // Média ponderada pelo valor investido
    const CDI_ATUAL = 13.65; // valor default, idealmente viria do backend
    let somaPonderada = 0;
    this.rendaFixaItems.controls.forEach(rf => {
      const valor = rf.controls.valor_investido.value || 0;
      let taxa = 0;
      if (rf.controls.tipo_taxa.value === 'pos_fixado') {
        const pct_cdi = rf.controls.percentual_cdi.value || 0;
        taxa = (pct_cdi / 100) * CDI_ATUAL;
      } else {
        taxa = rf.controls.taxa.value || 0;
      }
      somaPonderada += taxa * valor;
    });
    return somaPonderada / total;
  }

  rfTipoLabel(tipo: RendaFixaTipo): string {
    const labels: Record<RendaFixaTipo, string> = {
      cdb: 'CDB',
      lci: 'LCI',
      lca: 'LCA',
      tesouro_selic: 'Tesouro Selic',
      tesouro_ipca: 'Tesouro IPCA+',
      tesouro_pre: 'Tesouro Pré',
      lc: 'LC',
      cri: 'CRI',
      cra: 'CRA',
    };
    return labels[tipo];
  }

  evaluateAssets(): void {
    const items = this.portfolioItems.getRawValue();
    const dy = this.form.controls.desired_yield.getRawValue();
    this.svc.evaluatePortfolio({ items, desired_yield: dy }).subscribe({
      next: res => {
        this.result.set(res);
      },
      error: () => {},
      complete: () => {},
    });
  }

  private loadStoredPortfolio(): void {
    this.svc.getPortfolio().subscribe({
      next: res => {
        res.items.forEach(item => {
          const group = this.fb.group<PortfolioItemForm>({
            ticker: this.fb.control(item.ticker, {
              nonNullable: true,
              validators: Validators.required,
            }),
            quantity: this.fb.control(item.quantity, {
              nonNullable: true,
              validators: [Validators.required, Validators.min(0.0001)],
            }),
            avg_price: this.fb.control(item.avg_price, {
              nonNullable: true,
              validators: [Validators.required, Validators.min(0.0001)],
            }),
            category: this.fb.control(item.category, { nonNullable: true }),
          });
          this.portfolioItems.push(group);
        });
      },
      error: () => {},
    });
  }

  private persistPortfolio(): void {
    const items = this.portfolioItems.getRawValue();
    if (items.length === 0) return;

    this.saveState.set('saving');
    this.svc.savePortfolio(items).subscribe({
      next: () => {
        this.saveState.set('saved');
        setTimeout(() => this.saveState.set('idle'), 2000);
      },
      error: () => {
        this.saveState.set('error');
        setTimeout(() => this.saveState.set('idle'), 3000);
      },
      complete: () => {},
    });
  }

  private loadStoredRendaFixa(): void {
    const stored = localStorage.getItem('portfolio_renda_fixa');
    if (!stored) return;

    try {
      const items = JSON.parse(stored);
      items.forEach((item: any) => {
        const group = this.fb.group<RendaFixaItemForm>({
          nome: this.fb.control(item.nome || '', {
            nonNullable: true,
            validators: Validators.required,
          }),
          tipo: this.fb.control(item.tipo || 'cdb', { nonNullable: true }),
          valor_investido: this.fb.control(item.valor_investido || 0, {
            nonNullable: true,
            validators: [Validators.required, Validators.min(1)],
          }),
          taxa: this.fb.control(item.taxa || 0, {
            nonNullable: true,
            validators: [Validators.required, Validators.min(0)],
          }),
          prazo_meses: this.fb.control(item.prazo_meses || 0, {
            nonNullable: true,
            validators: [Validators.required, Validators.min(1)],
          }),
          data_aplicacao: this.fb.control(item.data_aplicacao || '', {
            nonNullable: true,
            validators: Validators.required,
          }),
          tipo_taxa: this.fb.control(item.tipo_taxa || 'pre_fixado', { nonNullable: true }),
          percentual_cdi: this.fb.control(item.percentual_cdi || null),
        });
        this.rendaFixaItems.push(group);
      });
    } catch (e) {
      console.error('Erro ao carregar renda fixa:', e);
    }
  }

  private persistRendaFixa(): void {
    const items = this.rendaFixaItems.getRawValue();
    localStorage.setItem('portfolio_renda_fixa', JSON.stringify(items));
  }
}
