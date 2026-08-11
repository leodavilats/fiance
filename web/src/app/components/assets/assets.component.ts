import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormControl,
  FormArray,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime, switchMap } from 'rxjs/operators';
import { HelpTooltipComponent } from '../help-tooltip/help-tooltip.component';
import {
  ClosedTradesResponse,
  LoadingService,
  PortfolioItem,
  PortfolioEvaluationResponse,
  PortfolioCategory,
  PortfolioPosition,
  RecommendService,
  RendaFixaTipo,
  SnackbarService,
  TickerSuggestion,
  UiHelperService,
} from '../../core';

interface PortfolioItemForm {
  ticker: FormControl<string>;
  quantity: FormControl<number>;
  avg_price: FormControl<number>;
  category: FormControl<PortfolioCategory>;
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
  oculto: FormControl<boolean>;
}

interface PortfolioFormShape {
  items: FormArray<FormGroup<PortfolioItemForm>>;
  renda_fixa: FormArray<FormGroup<RendaFixaItemForm>>;
}

@Component({
  selector: 'app-assets',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    LucideAngularModule,
    HelpTooltipComponent,
  ],
  templateUrl: './assets.component.html',
  styleUrls: ['./assets.component.scss'],
})
export class AssetsComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(RecommendService);
  private readonly snackbar = inject(SnackbarService);
  readonly loading = inject(LoadingService);
  readonly ui = inject(UiHelperService);

  form!: FormGroup<PortfolioFormShape>;

  result = signal<PortfolioEvaluationResponse | null>(null);
  saveState = signal<'idle' | 'saving' | 'saved' | 'error'>('idle');
  cdiAnual = signal(14.4);
  evaluating = signal(false);
  lastEvaluatedAt = signal<number | null>(null);
  lastEvaluatedLabel = computed(() => {
    const t = this.lastEvaluatedAt();
    return t ? new Date(t).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '';
  });

  expandedSections = {
    negociados: true,
    rendaFixa: true,
    avaliacao: false,
    detalhamentoRF: false,
  };

  rfVersion = signal(0);
  portfolioVersion = signal(0);

  closedTrades = signal<ClosedTradesResponse | null>(null);
  showClosedTrades = signal(false);
  sellModal = signal<{ position: PortfolioPosition; quantity: number; price: number } | null>(null);
  sellingInProgress = signal(false);
  expandedReasonsTicker = signal<string | null>(null);

  toggleReasons(ticker: string) {
    this.expandedReasonsTicker.set(this.expandedReasonsTicker() === ticker ? null : ticker);
  }

  tickerSuggestions = signal<TickerSuggestion[]>([]);
  tickerSuggestionsRow = signal<number | null>(null);
  private tickerSearch$ = new Subject<{ index: number; query: string }>();

  private _initialized = false;
  private saveDebounce = new Subject<void>();
  private evalDebounce = new Subject<void>();

  get portfolioItems() {
    return this.form.controls.items as FormArray<FormGroup<PortfolioItemForm>>;
  }

  get rendaFixaItems() {
    return this.form.controls.renda_fixa as FormArray<FormGroup<RendaFixaItemForm>>;
  }

  totalInvestido = computed(() => {
    this.portfolioVersion();
    const negociados = this.portfolioItems
      .getRawValue()
      .filter(x => x.ticker.trim() !== '')
      .reduce((sum, item) => sum + item.quantity * item.avg_price, 0);
    const rf = this.totalRendaFixa();
    return negociados + rf;
  });

  valorAtual = computed(() => {
    const r = this.result();
    if (!r) return this.totalInvestido();
    const negociados = r.total_current || 0;
    const rf = this.totalValorAtualRF();
    return negociados + rf;
  });

  rendimentoTotal = computed(() => {
    return this.valorAtual() - this.totalInvestido();
  });

  rendimentoPct = computed(() => {
    const invested = this.totalInvestido();
    if (invested === 0) return 0;
    return (this.rendimentoTotal() / invested) * 100;
  });

  negociadosCount = computed(() => {
    this.portfolioVersion();
    return this.portfolioItems.getRawValue().filter(x => x.ticker.trim() !== '').length;
  });

  totalAtivos = computed(() => {
    return this.negociadosCount() + this.rendaFixaItems.length;
  });

  totalRendaFixa = computed(() => {
    this.rfVersion();
    return this.rendaFixaItems
      .getRawValue()
      .filter(item => !item.oculto)
      .reduce((sum, item) => sum + (item.valor_investido || 0), 0);
  });

  totalRendimentoRF = computed(() => {
    this.rfVersion();
    let total = 0;
    for (let i = 0; i < this.rendaFixaItems.length; i++) {
      if (!this.rendaFixaItems.at(i).getRawValue().oculto) {
        total += this.calcularRendimento(i);
      }
    }
    return total;
  });

  totalValorAtualRF = computed(() => {
    return this.totalRendaFixa() + this.totalRendimentoRF();
  });

  totalValorFuturoRF = computed(() => {
    this.rfVersion();
    let total = 0;
    for (let i = 0; i < this.rendaFixaItems.length; i++) {
      if (!this.rendaFixaItems.at(i).getRawValue().oculto) {
        total += this.calcularValorFinal(i);
      }
    }
    return total;
  });

  alocacaoPorTipo = computed(() => {
    const total = this.valorAtual();
    if (total <= 0) return [];

    const buckets = new Map<string, number>();

    const rf = this.totalValorAtualRF();
    if (rf > 0) buckets.set('renda_fixa', rf);

    const r = this.result();
    if (r) {
      for (const p of r.positions) {
        const valor = p.current_value ?? p.invested;
        // Agrupa por categoria consolidada (não asset_type bruto) para bater
        // com o resto da tela — sem isso, BDR e Ação EUA apareciam como
        // fatias separadas em vez de "Ações Internacionais".
        const categoria = p.category_resolved;
        buckets.set(categoria, (buckets.get(categoria) || 0) + valor);
      }
    }

    return Array.from(buckets.entries())
      .map(([tipo, valor]) => ({ tipo, valor, pct: (valor / total) * 100 }))
      .sort((a, b) => b.valor - a.valor);
  });

  alocacaoPorSetor = computed(() => {
    const r = this.result();
    if (!r) return [];

    const STOCK_TYPES = new Set(['br_stock', 'bdr', 'us_stock']);
    const buckets = new Map<string, number>();
    let totalAcoes = 0;

    for (const p of r.positions) {
      if (!STOCK_TYPES.has(p.asset_type)) continue;
      const valor = p.current_value ?? p.invested;
      const setor = p.sector ? this.ui.translateSector(p.sector) : 'Outros';
      buckets.set(setor, (buckets.get(setor) || 0) + valor);
      totalAcoes += valor;
    }

    if (totalAcoes <= 0) return [];

    let entries = Array.from(buckets.entries())
      .map(([setor, valor]) => ({ setor, valor }))
      .sort((a, b) => b.valor - a.valor);

    const MAX_SEGMENTOS = 8;
    if (entries.length > MAX_SEGMENTOS) {
      const cauda = entries.slice(MAX_SEGMENTOS - 1);
      const outros = cauda.reduce((sum, e) => sum + e.valor, 0);
      entries = [...entries.slice(0, MAX_SEGMENTOS - 1), { setor: 'Outros', valor: outros }].sort(
        (a, b) => b.valor - a.valor
      );
    }

    return entries.map(e => ({ ...e, pct: (e.valor / totalAcoes) * 100 }));
  });

  avgTaxaRF = computed(() => {
    this.rfVersion();
    const items = this.rendaFixaItems.getRawValue().filter(item => !item.oculto);
    if (items.length === 0) return 0;

    let somaValorTaxa = 0;
    let somaValor = 0;

    items.forEach(item => {
      const taxa =
        item.tipo_taxa === 'pos_fixado'
          ? (item.percentual_cdi || 0) * (this.cdiAnual() / 100)
          : item.taxa;
      somaValorTaxa += item.valor_investido * taxa;
      somaValor += item.valor_investido;
    });

    return somaValor > 0 ? somaValorTaxa / somaValor : 0;
  });

  ngOnInit() {
    this.buildForm();
    this.svc.getReferencRates().subscribe({
      next: r => this.cdiAnual.set(r.cdi_anual),
      error: () => {},
    });
    this.loadStoredRendaFixa();
    this.loadStoredPortfolioItems();
    this.loadClosedTrades();
    this.saveDebounce.pipe(debounceTime(1000)).subscribe(() => this.savePortfolio());
    this.evalDebounce.pipe(debounceTime(1800)).subscribe(() => this.evaluateAssets(false));
    this.portfolioItems.valueChanges.subscribe(() => {
      this.portfolioVersion.update(v => v + 1);
      if (this._initialized) {
        this.saveDebounce.next();
        this.evalDebounce.next();
      }
    });
    this.rendaFixaItems.valueChanges.subscribe(() => {
      this.rfVersion.update(v => v + 1);
      if (this._initialized) this.saveDebounce.next();
    });

    this.tickerSearch$
      .pipe(
        debounceTime(250),
        switchMap(({ index, query }) => {
          if (query.trim().length < 1) return [{ index, items: [] as TickerSuggestion[] }];
          return this.svc
            .searchTickers(query)
            .pipe(switchMap(res => [{ index, items: res.items }]));
        })
      )
      .subscribe(({ index, items }) => {
        if (this.tickerSuggestionsRow() !== index) return;
        this.tickerSuggestions.set(items);
      });
  }

  onTickerInput(index: number, value: string) {
    this.tickerSuggestionsRow.set(index);
    this.tickerSearch$.next({ index, query: value });
  }

  selectTickerSuggestion(index: number, suggestion: TickerSuggestion) {
    this.portfolioItems.at(index).controls.ticker.setValue(suggestion.ticker);
    this.closeTickerSuggestions();
  }

  closeTickerSuggestions() {
    this.tickerSuggestionsRow.set(null);
    this.tickerSuggestions.set([]);
  }

  buildForm() {
    this.form = this.fb.group<PortfolioFormShape>({
      items: this.fb.array<FormGroup<PortfolioItemForm>>([]),
      renda_fixa: this.fb.array<FormGroup<RendaFixaItemForm>>([]),
    });
  }

  addItem() {
    const group = this.fb.group<PortfolioItemForm>({
      ticker: this.fb.control('', { nonNullable: true }),
      quantity: this.fb.control(0, { nonNullable: true }),
      avg_price: this.fb.control(0, { nonNullable: true }),
      category: this.fb.control('auto' as PortfolioCategory, { nonNullable: true }),
    });
    this.portfolioItems.push(group);
  }

  removeItem(group: FormGroup<PortfolioItemForm>) {
    const index = this.portfolioItems.controls.indexOf(group);
    if (index === -1) return;
    this.portfolioItems.removeAt(index);
    this.saveDebounce.next();
  }

  openSellModal(p: PortfolioPosition) {
    this.sellModal.set({
      position: p,
      quantity: p.quantity,
      price: p.current_price ?? p.avg_price,
    });
  }

  closeSellModal() {
    if (this.sellingInProgress()) return;
    this.sellModal.set(null);
  }

  updateSellQuantity(quantity: number) {
    const modal = this.sellModal();
    if (modal) this.sellModal.set({ ...modal, quantity });
  }

  updateSellPrice(price: number) {
    const modal = this.sellModal();
    if (modal) this.sellModal.set({ ...modal, price });
  }

  confirmSell() {
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
        this.snackbar.showSuccess(
          `Venda registrada: ${lucro} líquido de R$ ${Math.abs(trade.net_profit).toFixed(2)}` +
            (trade.ir_amount > 0 ? ` (IR: R$ ${trade.ir_amount.toFixed(2)})` : '')
        );
        this.loadClosedTrades();
        const idx = this.portfolioItems
          .getRawValue()
          .findIndex(i => i.ticker.toUpperCase() === position.ticker.toUpperCase());
        if (idx !== -1) {
          const remaining = position.quantity - quantity;
          if (remaining <= 1e-9) {
            this.portfolioItems.removeAt(idx);
          } else {
            this.portfolioItems.at(idx).controls.quantity.setValue(remaining);
          }
        }
      },
      error: err => {
        this.sellingInProgress.set(false);
        this.snackbar.showError(err?.error?.detail || 'Erro ao registrar venda.');
      },
    });
  }

  loadClosedTrades() {
    this.svc.getClosedTrades().subscribe({
      next: res => this.closedTrades.set(res),
      error: () => {},
    });
  }

  addRF() {
    this.saveDebounce.next();
    const group = this.fb.group<RendaFixaItemForm>({
      nome: this.fb.control('', { nonNullable: true, validators: Validators.required }),
      tipo: this.fb.control('cdb', { nonNullable: true }),
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
      tipo_taxa: this.fb.control('pre_fixado' as const, { nonNullable: true }),
      percentual_cdi: this.fb.control<number | null>(null),
      oculto: this.fb.control(false, { nonNullable: true }),
    });
    this.rendaFixaItems.push(group);
  }

  removeRF(group: FormGroup<RendaFixaItemForm>) {
    const index = this.rendaFixaItems.controls.indexOf(group);
    if (index === -1) return;
    this.rendaFixaItems.removeAt(index);
    this.saveDebounce.next();
  }

  toggleSection(section: 'negociados' | 'rendaFixa' | 'avaliacao' | 'detalhamentoRF') {
    this.expandedSections[section] = !this.expandedSections[section];
  }

  toggleOcultarRF(group: FormGroup<RendaFixaItemForm>) {
    group.controls.oculto.setValue(!group.controls.oculto.value);
    this.rfVersion.update(v => v + 1);
    this.saveDebounce.next();
  }

  async evaluateAssets(showLoader = true) {
    const items = this.portfolioItems.getRawValue().filter(x => x.ticker.trim() !== '');
    if (items.length === 0) return;

    if (showLoader) this.loading.show();
    else this.evaluating.set(true);

    this.svc
      .evaluatePortfolio({
        items,
      })
      .subscribe({
        next: res => {
          this.result.set(res);
          this.lastEvaluatedAt.set(Date.now());
          if (showLoader) this.loading.hide();
          else this.evaluating.set(false);
        },
        error: err => {
          console.error('Erro ao avaliar portfolio:', err);
          if (showLoader) this.loading.hide();
          else this.evaluating.set(false);
        },
      });
  }

  async savePortfolio() {
    const items = this.portfolioItems.getRawValue().filter(x => x.ticker.trim() !== '');

    const rfItems = this.rendaFixaItems.getRawValue();
    const rfPositions: PortfolioItem[] = rfItems.map((rf, idx) => ({
      ticker: `RF_${rf.tipo}_${idx + 1}`,
      quantity: 1,
      avg_price: rf.valor_investido,
      category: 'renda_fixa',
    }));

    const allItems = [...items, ...rfPositions];
    if (allItems.length === 0) return;

    this.saveState.set('saving');
    this.svc.savePortfolio(allItems).subscribe({
      next: () => {
        this.saveState.set('saved');

        this.persistRendaFixa();
        setTimeout(() => this.saveState.set('idle'), 2000);
      },
      error: () => {
        this.saveState.set('error');
        setTimeout(() => this.saveState.set('idle'), 3000);
      },
      complete: () => {},
    });
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
    return labels[tipo] || tipo;
  }

  isIsentoIR(tipo: RendaFixaTipo): boolean {
    return ['lci', 'lca', 'cri', 'cra'].includes(tipo);
  }

  calcularRendimento(index: number): number {
    const item = this.rendaFixaItems.at(index)?.getRawValue();
    if (!item) return 0;

    const CDI_ANUAL = this.cdiAnual();

    let taxaAnual = 0;
    if (item.tipo_taxa === 'pos_fixado') {
      taxaAnual = ((item.percentual_cdi || 100) / 100) * CDI_ANUAL;
    } else {
      taxaAnual = item.taxa;
    }

    const dataAplicacao = new Date(item.data_aplicacao);
    const hoje = new Date();
    const diasCorridos = isNaN(dataAplicacao.getTime())
      ? 0
      : Math.max(0, Math.floor((hoje.getTime() - dataAplicacao.getTime()) / (1000 * 60 * 60 * 24)));

    const rendimentoBruto =
      item.valor_investido * (Math.pow(1 + taxaAnual / 100, diasCorridos / 365) - 1);

    if (this.isIsentoIR(item.tipo)) {
      return rendimentoBruto;
    }

    let aliquotaIR = 0.225;
    if (diasCorridos > 720) aliquotaIR = 0.15;
    else if (diasCorridos > 360) aliquotaIR = 0.175;
    else if (diasCorridos > 180) aliquotaIR = 0.2;

    return rendimentoBruto * (1 - aliquotaIR);
  }

  calcularValorFinal(index: number): number {
    const item = this.rendaFixaItems.at(index)?.getRawValue();
    if (!item) return 0;

    const CDI_ANUAL = this.cdiAnual();

    let taxaAnual = 0;
    if (item.tipo_taxa === 'pos_fixado') {
      taxaAnual = ((item.percentual_cdi || 100) / 100) * CDI_ANUAL;
    } else {
      taxaAnual = item.taxa;
    }

    const montanteBruto =
      item.valor_investido * Math.pow(1 + taxaAnual / 100, item.prazo_meses / 12);
    const rendimentoBruto = montanteBruto - item.valor_investido;

    if (this.isIsentoIR(item.tipo)) {
      return montanteBruto;
    }

    const diasTotais = item.prazo_meses * 30;
    let aliquotaIR = 0.225;
    if (diasTotais > 720) aliquotaIR = 0.15;
    else if (diasTotais > 360) aliquotaIR = 0.175;
    else if (diasTotais > 180) aliquotaIR = 0.2;

    return item.valor_investido + rendimentoBruto * (1 - aliquotaIR);
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
          oculto: this.fb.control(item.oculto ?? false, { nonNullable: true }),
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

  private loadStoredPortfolioItems(): void {
    this.svc.getPortfolio().subscribe({
      next: res => {
        const realItems = res.items.filter(item => !item.ticker.startsWith('RF_'));

        if (this.rendaFixaItems.length === 0) {
          const backendRfItems = res.items.filter(item => item.ticker.startsWith('RF_'));
          if (backendRfItems.length > 0) {
            backendRfItems.forEach(rfItem => {
              const parts = rfItem.ticker.split('_');
              const tipo = (parts[1] || 'cdb') as RendaFixaTipo;
              const group = this.fb.group<RendaFixaItemForm>({
                nome: this.fb.control('', { nonNullable: true, validators: Validators.required }),
                tipo: this.fb.control(tipo, { nonNullable: true }),
                valor_investido: this.fb.control(rfItem.avg_price, {
                  nonNullable: true,
                  validators: [Validators.required, Validators.min(1)],
                }),
                taxa: this.fb.control(0, {
                  nonNullable: true,
                  validators: [Validators.required, Validators.min(0)],
                }),
                prazo_meses: this.fb.control(12, {
                  nonNullable: true,
                  validators: [Validators.required, Validators.min(1)],
                }),
                data_aplicacao: this.fb.control('', {
                  nonNullable: true,
                  validators: Validators.required,
                }),
                tipo_taxa: this.fb.control('pre_fixado' as const, { nonNullable: true }),
                percentual_cdi: this.fb.control<number | null>(null),
                oculto: this.fb.control(false, { nonNullable: true }),
              });
              this.rendaFixaItems.push(group);
            });
            this.persistRendaFixa();
          }
        }

        if (realItems.length > 0) {
          realItems.forEach(item => {
            const group = this.fb.group<PortfolioItemForm>({
              ticker: this.fb.control(item.ticker, { nonNullable: true }),
              quantity: this.fb.control(item.quantity, { nonNullable: true }),
              avg_price: this.fb.control(item.avg_price, { nonNullable: true }),
              category: this.fb.control(item.category as PortfolioCategory, { nonNullable: true }),
            });
            this.portfolioItems.push(group);
          });
          this.evaluateAssets();
        } else {
          this.addItem();
        }

        this._initialized = true;
        if (this.rendaFixaItems.length > 0) {
          this.savePortfolio();
        }
      },
      error: () => {
        this.addItem();
        this._initialized = true;
      },
    });
  }
}
