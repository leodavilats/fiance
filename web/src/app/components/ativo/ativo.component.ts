import { CommonModule, DOCUMENT } from '@angular/common';
import {
  Component,
  computed,
  inject,
  OnDestroy,
  OnInit,
  REQUEST,
  RESPONSE_INIT,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Meta, Title } from '@angular/platform-browser';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime, switchMap, takeUntil } from 'rxjs/operators';
import {
  AssetAnalysis,
  AssetType,
  AuthService,
  CarteiraStore,
  FiState,
  LoadingService,
  NavegacaoService,
  RecommendService,
  TickerSuggestion,
  UiHelperService,
  fiDecision,
} from '../../core';
import { environment } from '../../../environments/environment';
import { AssetPriceChartComponent } from '../asset-price-chart/asset-price-chart.component';
import { MetricWithContextComponent } from '../metric-with-context/metric-with-context.component';
import { MarginOfSafetyComponent } from '../margin-of-safety/margin-of-safety.component';
import { SkeletonComponent } from '../skeleton/skeleton.component';

export interface ValuationMethod {
  readonly name: string;
  readonly price: number | null;
  readonly upsidePct: number | null;
  readonly methodology: string;
  readonly notApplicable: string | null;
}

interface Fundamental {
  readonly label: string;
  /** Já formatado. `null` quando a fonte não trouxe o indicador. */
  readonly value: string | null;
  readonly hint: string;
  /**
   * A referência que torna o número interpretável, quando ela existe.
   *
   * Sai das mesmas frases do glossário do produto — não são limiares novos, e
   * indicador sem referência declarada simplesmente não ganha uma (§206).
   */
  readonly anchor: string;
}

@Component({
  selector: 'app-ativo',
  standalone: true,
  imports: [
    AssetPriceChartComponent,
    CommonModule,
    LucideAngularModule,
    MarginOfSafetyComponent,
    MetricWithContextComponent,
    ReactiveFormsModule,
    RouterLink,
    SkeletonComponent,
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
  private readonly carteira = inject(CarteiraStore);
  private readonly navegacao = inject(NavegacaoService);
  private readonly auth = inject(AuthService);
  private readonly title = inject(Title);
  private readonly meta = inject(Meta);
  private readonly doc = inject(DOCUMENT);
  /** Nulo no navegador; no SSR é o init da resposta que o Express vai devolver. */
  private readonly responseInit = inject(RESPONSE_INIT, { optional: true });
  private readonly request = inject(REQUEST, { optional: true });

  /** Se há sessão, a página é a do usuário; se não, é a página pública. */
  readonly isAnonymous = computed(() => !this.auth.isAuthenticated());

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
      if (this.auth.isAuthenticated()) this.carteira.ensureLoaded();
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

  /**
   * Título e descrição por ticker.
   *
   * É o que separa "uma página indexada" de "seiscentas páginas iguais": sem
   * conteúdo próprio por ticker, a busca trata o conjunto como duplicado e não
   * indexa nenhuma. O veredito e o preço justo entram no resumo porque são a
   * resposta que a pessoa foi procurar.
   */
  private describePage(asset: AssetAnalysis): void {
    const nome = asset.name ? `${asset.name} (${asset.symbol})` : asset.symbol;
    this.title.setTitle(`${nome} — preço justo, valuation e score | fiance`);

    const justo = asset.fair_price?.consensus;
    const trecho = justo
      ? `Preço justo estimado de R$ ${justo.toFixed(2)} contra R$ ${(asset.price ?? 0).toFixed(2)} de mercado.`
      : 'Valuation por múltiplos métodos, com a metodologia à vista.';

    const descricao =
      `${nome}: ${asset.decision.label.toLowerCase()}. ${trecho} ` +
      `Score, margem de segurança e histórico de proventos, com o cálculo explicado.`;

    const canonica = this.absoluta(`/ativo/${asset.symbol}`);

    this.meta.updateTag({ name: 'description', content: descricao });
    this.meta.updateTag({ property: 'og:title', content: `${nome} | fiance` });
    this.meta.updateTag({ property: 'og:description', content: descricao });
    this.meta.updateTag({ property: 'og:type', content: 'article' });
    this.meta.updateTag({ property: 'og:url', content: canonica });

    // Sem imagem, todo link compartilhado sai como um retângulo de texto — e a
    // distribuição orgânica de conteúdo financeiro no Brasil é WhatsApp,
    // LinkedIn e X. A imagem é gerada por ticker no backend, com o preço justo
    // e o veredito, que é a resposta que a pessoa foi procurar.
    const imagem = `${environment.apiBaseUrl}/public/asset/${asset.symbol}/og.png`;
    this.meta.updateTag({ property: 'og:image', content: imagem });
    this.meta.updateTag({ property: 'og:image:width', content: '1200' });
    this.meta.updateTag({ property: 'og:image:height', content: '630' });
    this.meta.updateTag({ property: 'og:image:alt', content: `${nome}: ${asset.decision.label}` });
    this.meta.updateTag({ name: 'twitter:card', content: 'summary_large_image' });
    this.meta.updateTag({ name: 'twitter:title', content: `${nome} | fiance` });
    this.meta.updateTag({ name: 'twitter:description', content: descricao });
    this.meta.updateTag({ name: 'twitter:image', content: imagem });

    this.permitirIndexacao();
    this.setCanonical(canonica);
    this.setDadoEstruturado(asset, descricao, canonica);
  }

  /**
   * O que a página diz quando a análise não sai.
   *
   * `describePage` só rodava no caminho feliz. Um 404 de ticker ou uma queda da
   * fonte devolvia HTTP 200 com o título genérico do index.html — e o sitemap
   * anuncia ~400 tickers, então uma indisponibilidade durante uma varredura
   * produzia centenas de páginas idênticas, que é exatamente o conteúdo
   * duplicado que a canônica existe para evitar. Agora o status é real e a
   * página se marca como não indexável.
   */
  private describeFailure(symbol: string, notFound: boolean): void {
    const alvo = symbol.toUpperCase();

    this.title.setTitle(
      notFound ? `${alvo} não encontrado | fiance` : `${alvo} indisponível | fiance`
    );
    this.meta.updateTag({
      name: 'description',
      content: notFound
        ? `Não encontramos o ativo ${alvo} na B3.`
        : `A análise de ${alvo} está temporariamente indisponível.`,
    });
    this.meta.updateTag({ name: 'robots', content: 'noindex, follow' });
    this.removerDadoEstruturado();

    if (this.responseInit) this.responseInit.status = notFound ? 404 : 503;
  }

  private permitirIndexacao(): void {
    this.meta.removeTag("name='robots'");
    if (this.responseInit) this.responseInit.status = 200;
  }

  /**
   * A origem pública, sem fixá-la em build.
   *
   * Uma canônica relativa resolve, mas não normaliza host nem protocolo — que é
   * justamente o problema que uma canônica costuma existir para resolver.
   */
  private absoluta(path: string): string {
    if (this.request) {
      try {
        return new URL(path, this.request.url).toString();
      } catch {
        /* cai no caminho de baixo */
      }
    }

    const location = this.doc.defaultView?.location;
    return location ? new URL(path, location.origin).toString() : path;
  }

  /**
   * JSON-LD.
   *
   * Diz ao buscador que a página é uma análise de um instrumento financeiro
   * nomeado, em vez de deixá-lo inferir de um bloco de texto.
   */
  private setDadoEstruturado(asset: AssetAnalysis, descricao: string, url: string): void {
    const dados = {
      '@context': 'https://schema.org',
      '@type': 'WebPage',
      name: `${asset.name ?? asset.symbol} (${asset.symbol})`,
      description: descricao,
      url,
      about: {
        '@type': 'Corporation',
        name: asset.name ?? asset.symbol,
        tickerSymbol: asset.symbol,
      },
      isPartOf: { '@type': 'WebSite', name: 'fiance', url: this.absoluta('/') },
    };

    this.removerDadoEstruturado();
    const script = this.doc.createElement('script');
    script.type = 'application/ld+json';
    script.id = 'fi-jsonld';
    script.textContent = JSON.stringify(dados);
    this.doc.head.appendChild(script);
  }

  private removerDadoEstruturado(): void {
    this.doc.head.querySelector('#fi-jsonld')?.remove();
  }

  /**
   * Canônica é `<link>`, não `<meta>` — o `Meta` do Angular só gerencia meta
   * tags, e pedir a ele um rel=canonical produz uma tag que nenhum buscador lê.
   *
   * Sem ela, `/ativo/PETR4` e `/ativo/petr4` viram conteúdo duplicado e as duas
   * perdem posição.
   */
  private setCanonical(href: string): void {
    const existing = this.doc.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    if (existing) {
      existing.href = href;
      return;
    }
    const link = this.doc.createElement('link');
    link.rel = 'canonical';
    link.href = href;
    this.doc.head.appendChild(link);
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
        this.describePage(res);
      },
      error: err => {
        this.analysis.set(null);
        this.fetching.set(false);
        const naoExiste = err?.status === 404;
        if (naoExiste) this.notFound.set(symbol);
        else this.failed.set(true);
        this.describeFailure(symbol, naoExiste);
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

  /** O backend devolve a margem como fração; a régua lê percentual. */
  readonly marginPct = computed(() => {
    const m = this.analysis()?.fair_price.margin_of_safety;
    return m == null ? null : m * 100;
  });

  /**
   * Preço médio da posição, quando o ativo está na carteira — a linha que
   * transforma "está barato?" em "está barato **para mim**?". Sem posição, a
   * linha simplesmente não existe: nada de desenhar zero.
   */
  /**
   * A posição da pessoa neste ativo, quando existe.
   *
   * É o que faz a oportunidade vista em Descobrir e a posição vista na
   * Carteira se reconhecerem aqui: sem isto, a camada de ativo é uma página
   * sobre um papel qualquer, igual para quem tem 200 cotas e para quem nunca
   * ouviu falar dele.
   */
  readonly posicao = computed(() => {
    const symbol = this.analysis()?.symbol;
    if (!symbol) return null;
    return (
      this.carteira.tradedPositions().find(p => p.ticker.toUpperCase() === symbol.toUpperCase()) ??
      null
    );
  });

  readonly carteiraCarregada = computed(() => this.carteira.tradedPositions().length > 0);

  readonly averagePrice = computed(() => this.posicao()?.avg_price ?? null);

  /** De onde a pessoa veio, quando veio de dentro do app. */
  origem() {
    return this.navegacao.origem();
  }

  /** Os filtros da lista de origem, preservados na volta. */
  paramsDaOrigem(url: string): Record<string, string> {
    const query = url.split('?')[1];
    if (!query) return {};
    return Object.fromEntries(new URLSearchParams(query));
  }

  absoluto(valor: number): number {
    return Math.abs(valor);
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
      hint: string,
      anchor = ''
    ) => {
      rows.push({ label, value: value == null ? null : fmt(value), hint, anchor });
    };

    const pct = (v: number) => `${v.toFixed(1)}%`;
    const num = (v: number) => v.toFixed(2);

    push('P/L', f.pe_ratio, num, 'Preço sobre lucro por ação.');
    push(
      'P/VP',
      f.pb_ratio,
      num,
      'Preço sobre valor patrimonial.',
      'abaixo de 1 é desconto patrimonial'
    );
    push(
      'ROE',
      f.roe,
      pct,
      'Retorno sobre o patrimônio líquido.',
      'acima de 15% a.a. é considerado bom'
    );
    push('Margem líquida', f.profit_margin, pct, 'Quanto da receita sobra como lucro.');
    push(
      'Dívida/Patrimônio',
      f.debt_to_equity,
      num,
      'Endividamento sobre o patrimônio.',
      'abaixo de 100% é confortável'
    );
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
