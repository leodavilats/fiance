import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime, switchMap, takeUntil } from 'rxjs/operators';
import {
  AssetAnalysis,
  AssetType,
  FiState,
  LoadingService,
  RecommendService,
  TickerSuggestion,
  UiHelperService,
  fiDecision,
} from '../../core';
import { ScoreRulerComponent } from '../score-ruler/score-ruler.component';

export interface ValuationMethod {
  readonly name: string;
  readonly price: number | null;
  readonly upsidePct: number | null;
  readonly methodology: string;
  readonly notApplicable: string | null;
}

interface Fundamental {
  readonly label: string;
  readonly value: string;
  readonly hint: string;
}

@Component({
  selector: 'app-ativo',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    LucideAngularModule,
    RouterLink,
    ScoreRulerComponent,
  ],
  templateUrl: './ativo.component.html',
})
export class AtivoComponent implements OnInit, OnDestroy {
  private readonly api = inject(RecommendService);
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  private readonly destroy$ = new Subject<void>();
  private readonly search$ = new Subject<string>();

  readonly analysis = signal<AssetAnalysis | null>(null);
  readonly fetching = signal(false);
  readonly notFound = signal<string | null>(null);
  readonly failed = signal(false);
  readonly showMethod = signal(false);

  readonly suggestions = signal<TickerSuggestion[]>([]);
  readonly suggestionsOpen = signal(false);

  readonly searchForm = this.fb.nonNullable.group({
    symbol: ['', Validators.required],
  });

  ngOnInit(): void {
    this.route.paramMap.pipe(takeUntil(this.destroy$)).subscribe(params => {
      const ticker = params.get('ticker');
      if (!ticker) {
        this.analysis.set(null);
        return;
      }
      const symbol = ticker.toUpperCase();
      this.searchForm.controls.symbol.setValue(symbol);
      this.fetch(symbol);
    });

    this.search$
      .pipe(
        debounceTime(250),
        switchMap(query => {
          if (query.trim().length < 1) return [[] as TickerSuggestion[]];
          return this.api.searchTickers(query).pipe(switchMap(res => [res.items]));
        }),
        takeUntil(this.destroy$)
      )
      .subscribe(items => this.suggestions.set(items));
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private fetch(symbol: string): void {
    this.fetching.set(true);
    this.notFound.set(null);
    this.failed.set(false);
    this.api.analyzeAsset(symbol).subscribe({
      next: res => {
        this.analysis.set(res);
        this.fetching.set(false);
      },
      error: err => {
        this.analysis.set(null);
        this.fetching.set(false);
        if (err?.status === 404) this.notFound.set(symbol);
        else this.failed.set(true);
      },
    });
  }

  onSymbolInput(value: string): void {
    this.suggestionsOpen.set(true);
    this.search$.next(value);
  }

  selectSuggestion(s: TickerSuggestion): void {
    this.closeSuggestions();
    this.router.navigate(['/ativo', s.ticker]);
  }

  closeSuggestions(): void {
    this.suggestionsOpen.set(false);
    this.suggestions.set([]);
  }

  submitSearch(): void {
    const symbol = this.searchForm.getRawValue().symbol.trim().toUpperCase();
    if (!symbol) return;
    this.closeSuggestions();
    this.router.navigate(['/ativo', symbol]);
  }

  readonly summary = computed(() => {
    const a = this.analysis();
    if (!a) return '';

    const parts: string[] = [];
    const mos = a.fair_price.margin_of_safety;
    if (mos != null && a.fair_price.consensus != null) {
      const pct = Math.abs(Math.round(mos * 100));
      parts.push(
        mos > 0
          ? `Negociando ${pct}% abaixo do preço justo estimado`
          : mos < 0
            ? `Negociando ${pct}% acima do preço justo estimado`
            : 'Negociando no preço justo estimado'
      );
    }

    const trend = a.technical.trend;
    if (trend && trend !== 'unknown') {
      parts.push(`com tendência ${this.ui.trendLabel(trend).toLowerCase()}`);
    }

    if (parts.length === 0) {
      return 'Não há dado suficiente para uma leitura de valuation deste ativo.';
    }
    return `${parts.join(', ')}.`;
  });

  readonly decision = computed<{ label: string; state: FiState } | null>(() => {
    const v = this.analysis()?.decision.verdict;
    if (!v) return null;
    switch (v) {
      case 'STRONG_BUY':
      case 'BUY':
        return fiDecision.interesting;
      case 'HOLD':
        return fiDecision.neutral;
      case 'SELL':
        return fiDecision.attention;
      case 'STRONG_SELL':
        return fiDecision.avoid;
      default:
        return fiDecision.unknown;
    }
  });

  decisionClass(): string {
    switch (this.decision()?.state) {
      case 'favorable':
        return 'text-favorable';
      case 'attention':
        return 'text-attention';
      case 'adverse':
        return 'text-adverse';
      case 'indeterminate':
        return 'text-indeterminate';
      default:
        return 'text-ink-2';
    }
  }

  readonly confidenceScore = computed(() => (this.analysis()?.decision.confidence ?? 0) * 100);

  readonly methods = computed<ValuationMethod[]>(() => {
    const a = this.analysis();
    if (!a) return [];

    const fp = a.fair_price;
    const price = a.price;
    const yieldPct = (fp.desired_yield_used ?? 0) * 100;
    const type = a.asset_type;

    const upside = (target: number | null): number | null =>
      target != null && price != null && price > 0 ? ((target - price) / price) * 100 : null;

    const rows: ValuationMethod[] = [
      {
        name: 'Bazin',
        price: fp.bazin,
        upsidePct: upside(fp.bazin),
        methodology:
          fp.data_years > 0
            ? `Dividendo médio de ${fp.data_years} ${fp.data_years === 1 ? 'ano' : 'anos'} ÷ meta de yield de ${yieldPct.toFixed(0)}%`
            : `Dividendo anual ÷ meta de yield de ${yieldPct.toFixed(0)}%`,
        notApplicable: fp.bazin == null ? this.bazinAbsence(a) : null,
      },
      {
        name: 'Graham',
        price: fp.graham,
        upsidePct: upside(fp.graham),
        methodology: '√(22,5 × LPA × VPA)',
        notApplicable: fp.graham == null ? this.grahamAbsence(type, a) : null,
      },
      {
        name: 'DCF',
        price: fp.dcf,
        upsidePct: upside(fp.dcf),
        methodology: this.dcfMethodology(a),
        notApplicable: fp.dcf == null ? this.dcfAbsence(type, a) : null,
      },
    ];

    if (type === 'fii' && fp.details?.['pvp_fair'] != null) {
      rows.push({
        name: 'P/VP justo',
        price: fp.details['pvp_fair'],
        upsidePct: upside(fp.details['pvp_fair']),
        methodology: 'Valor patrimonial da cota (P/VP = 1)',
        notApplicable: null,
      });
    }

    return rows;
  });

  private bazinAbsence(a: AssetAnalysis): string {
    if (a.fair_price.data_years === 0) return 'Sem histórico de proventos encontrado.';
    return 'Não foi possível estimar com os proventos disponíveis.';
  }

  private grahamAbsence(type: AssetType, a: AssetAnalysis): string {
    if (type === 'fii') return 'Graham não se aplica a fundo imobiliário.';
    if (type === 'etf') return 'Graham não se aplica a ETF: não há LPA nem VPA de empresa.';
    if (a.fundamentals.book_value == null) {
      return 'Valor patrimonial por ação não disponível na fonte.';
    }
    if ((a.fundamentals.eps ?? 0) <= 0) return 'Lucro por ação não positivo.';
    return 'Fora das condições do método (P/L ≤ 15 e P/VP ≤ 1,5).';
  }

  private dcfAbsence(type: AssetType, a: AssetAnalysis): string {
    if (type === 'fii') return 'Fluxo descontado não se aplica a fundo imobiliário.';
    if (type === 'etf') return 'Fluxo descontado não se aplica a ETF.';
    if ((a.fundamentals.eps ?? 0) <= 0) return 'Lucro por ação não positivo.';
    return 'Insumos insuficientes para projetar o fluxo.';
  }

  private dcfMethodology(a: AssetAnalysis): string {
    const growth = a.fundamentals.revenue_growth;
    return growth != null
      ? `Fluxo descontado, crescimento de ${growth.toFixed(1)}% a.a.`
      : 'Fluxo de caixa descontado';
  }

  readonly consensusProvenance = computed(() => {
    const a = this.analysis();
    if (!a) return '';
    return [
      this.ui.consensusLabel(a.fair_price.consensus_methods),
      this.ui.dataYearsLabel(a.fair_price.data_years),
      this.ui.confidenceLabel(a.decision.confidence),
    ]
      .filter(Boolean)
      .join(' · ');
  });

  readonly fundamentals = computed<Fundamental[]>(() => {
    const a = this.analysis();
    if (!a) return [];
    const f = a.fundamentals;
    const rows: Fundamental[] = [];

    const push = (
      label: string,
      value: number | null | undefined,
      fmt: (v: number) => string,
      hint: string
    ) => {
      if (value == null) return;
      rows.push({ label, value: fmt(value), hint });
    };

    const pct = (v: number) => `${v.toFixed(1)}%`;
    const num = (v: number) => v.toFixed(2);

    push('P/L', f.pe_ratio, num, 'Preço sobre lucro por ação.');
    push('P/VP', f.pb_ratio, num, 'Preço sobre valor patrimonial.');
    push('ROE', f.roe, pct, 'Retorno sobre o patrimônio líquido.');
    push('Margem líquida', f.profit_margin, pct, 'Quanto da receita sobra como lucro.');
    push('Dívida/Patrimônio', f.debt_to_equity, num, 'Endividamento sobre o patrimônio.');
    push('Crescimento de receita', f.revenue_growth, pct, 'Variação da receita.');
    return rows;
  });

  createAlert(): void {
    const symbol = this.analysis()?.symbol;
    if (!symbol) return;
    this.router.navigate(['/voce/alertas'], { queryParams: { ticker: symbol } });
  }

  compare(): void {
    const symbol = this.analysis()?.symbol;
    if (!symbol) return;
    this.router.navigate(['/descobrir/comparar'], { queryParams: { tickers: symbol } });
  }

  understandDip(): void {
    const symbol = this.analysis()?.symbol;
    if (!symbol) return;
    this.router.navigate(['/descobrir/quedas']);
  }

  retry(): void {
    const symbol = this.analysis()?.symbol ?? this.searchForm.getRawValue().symbol;
    if (symbol) this.fetch(symbol.toUpperCase());
  }

  toggleMethod(): void {
    this.showMethod.update(v => !v);
  }
}
