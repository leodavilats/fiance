import { Injectable } from '@angular/core';
import { AssetType, Verdict } from '../models';
import {
  MIN_DATA_COMPLETENESS,
  SCORE_GLOSSARY,
  ScoreBand,
  dataCompletenessLabel,
  scoreBandFor,
} from '../score-ruler';
import {
  fiCategoriaApelidos,
  fiCategorias,
  fiClasseBarraDaSerie,
  fiClasseChipDaSerie,
  fiClasseTextoDaSerie,
  fiSetorApelidos,
  fiSetorSeriePorRotulo,
  fiSetores,
  fiTiposDeAtivo,
} from '../vocabulary';

@Injectable({ providedIn: 'root' })
export class UiHelperService {
  formatTimestamp(ts: number): string {
    return new Date(ts * 1000).toLocaleString('pt-BR');
  }

  assetTypeLabel(t: AssetType | string): string {
    return fiTiposDeAtivo[t]?.label ?? String(t);
  }

  sectorLabel(setor: string): string {
    return fiSetores[setor]?.label ?? fiSetorApelidos[setor] ?? setor;
  }

  sectorSeriesColor(sectorLabel: string): string {
    const serie = fiSetorSeriePorRotulo[sectorLabel];
    return serie ? `var(--fi-series-${serie})` : 'var(--fi-series-other)';
  }

  private serieDaCategoria(c: string): number {
    const chave = fiCategoriaApelidos[c] ?? c;
    return fiCategorias[chave]?.series ?? 0;
  }

  categoryLabel(c: string): string {
    const chave = fiCategoriaApelidos[c] ?? c;
    return fiCategorias[chave]?.label ?? c;
  }

  categoryIcon(c: string): string {
    const chave = fiCategoriaApelidos[c] ?? c;
    return fiCategorias[chave]?.icon ?? 'circle';
  }

  categoryColor(c: string): string {
    return fiClasseTextoDaSerie[this.serieDaCategoria(c)] ?? 'text-series-other';
  }

  categoryBarClass(c: string): string {
    return fiClasseBarraDaSerie[this.serieDaCategoria(c)] ?? 'bg-series-other';
  }

  categoryBgClass(c: string): string {
    return fiClasseChipDaSerie[this.serieDaCategoria(c)] ?? 'bg-series-other/15';
  }

  categoryBarColor(c: string): string {
    const n = this.serieDaCategoria(c);
    return n ? `var(--fi-series-${n})` : 'var(--fi-series-other)';
  }

  verdictClass(v: Verdict): string {
    const map: Record<Verdict, string> = {
      STRONG_BUY: 'v-buy',
      BUY: 'v-buy',
      HOLD: 'v-hold',
      SELL: 'v-sell',
      STRONG_SELL: 'v-sell',
      UNKNOWN: 'v-unknown',
    };
    return map[v] || 'v-unknown';
  }

  trendLabel(t: string): string {
    const map: Record<string, string> = {
      uptrend: '↗ Alta',
      downtrend: '↘ Baixa',
      sideways: '→ Lateral',
    };
    return map[t] || t;
  }

  translateSector(s: string | null): string {
    if (!s) return '—';
    const map: Record<string, string> = {
      'Financial Services': 'Financeiro',
      Technology: 'Tecnologia',
      Healthcare: 'Saúde',
      Energy: 'Energia',
      'Basic Materials': 'Materiais Básicos',
      Industrials: 'Industrial',
      'Consumer Cyclical': 'Consumo Cíclico',
      'Consumer Defensive': 'Consumo Básico',
      'Real Estate': 'Imobiliário',
      Utilities: 'Utilidades Públicas',
      'Communication Services': 'Telecomunicações',
      technology: 'Tecnologia',
      finance: 'Financeiro',
      healthcare: 'Saúde',
      energy: 'Energia',
      utilities: 'Utilidades Públicas',
      'consumer-discretionary': 'Consumo Cíclico',
      'consumer-staples': 'Consumo Básico',
      industrials: 'Industrial',
      materials: 'Materiais Básicos',
      'real-estate': 'Imobiliário',
      telecommunications: 'Telecomunicações',
      Miscellaneous: 'Outros',
      Finance: 'Financeiro',
      'Technology Services': 'Tecnologia',
      'Electronic Technology': 'Tecnologia',
      'Producer Manufacturing': 'Industrial',
      'Industrial Services': 'Industrial',
      'Retail Trade': 'Consumo Cíclico',
      'Consumer Services': 'Consumo Cíclico',
      'Consumer Durables': 'Consumo Cíclico',
      'Process Industries': 'Materiais Básicos',
      'Non-Energy Minerals': 'Materiais Básicos',
      'Health Technology': 'Saúde',
      'Health Services': 'Saúde',
      'Consumer Non-Durables': 'Consumo Básico',
      'Commercial Services': 'Industrial',
      Transportation: 'Industrial',
      'Energy Minerals': 'Energia',
      Communications: 'Telecomunicações',
      'Distribution Services': 'Industrial',
    };
    return map[s] || s;
  }

  sectorIcon(s: string): string {
    const map: Record<string, string> = {
      Financeiro: 'landmark',
      'Financial Services': 'landmark',
      Tecnologia: 'cpu',
      Technology: 'cpu',
      Saúde: 'heart-pulse',
      Healthcare: 'heart-pulse',
      Energia: 'zap',
      Energy: 'zap',
      'Materiais Básicos': 'gem',
      'Basic Materials': 'gem',
      Industrial: 'factory',
      Industrials: 'factory',
      'Consumo Cíclico': 'shopping-bag',
      'Consumer Cyclical': 'shopping-bag',
      'Consumo Básico': 'shopping-cart',
      'Consumer Defensive': 'shopping-cart',
      Imobiliário: 'building-2',
      'Real Estate': 'building-2',
      'Utilidades Públicas': 'plug-zap',
      Utilities: 'plug-zap',
      Telecomunicações: 'wifi',
      'Communication Services': 'wifi',
      Outros: 'circle-dot',
    };
    return map[s] || 'chart-bar';
  }

  toNum(v: string | number | null): number | null {
    if (typeof v === 'number') return v;
    if (!v || v.trim() === '') return null;
    const parsed = parseFloat(v);
    return isNaN(parsed) ? null : parsed;
  }

  scoreIsReliable(dataCompleteness: number | null | undefined): boolean {
    return (dataCompleteness ?? 1) >= MIN_DATA_COMPLETENESS;
  }

  scoreBandFor(score: number, dataCompleteness: number | null | undefined): ScoreBand {
    return scoreBandFor(score, dataCompleteness);
  }

  dataCompletenessLabel(dataCompleteness: number | null | undefined): string {
    return dataCompletenessLabel(dataCompleteness);
  }

  trendBasisLabel(basis: string | null | undefined): string {
    const map: Record<string, string> = {
      long: 'médias de 50 e 200 dias',
      short: 'médias de 20 e 50 dias (histórico curto)',
      none: 'sem histórico suficiente',
    };
    return map[basis ?? 'none'] ?? '';
  }

  dataYearsLabel(dataYears: number | null | undefined): string {
    if (!dataYears) return 'sem histórico de proventos';
    return `${dataYears} ${dataYears === 1 ? 'ano' : 'anos'} de proventos`;
  }

  consensusLabel(methods: number | null | undefined): string {
    if (!methods) return 'sem método aplicável';
    return `${methods} ${methods === 1 ? 'método' : 'métodos'} no consenso`;
  }

  confidenceLabel(confidence: number | null | undefined): string {
    if (confidence == null) return '';
    return `confiança ${Math.round(confidence * 100)}%`;
  }

  readonly glossary: Record<string, string> = {
    dy: 'Dividend Yield — percentual do preço atual pago em dividendos nos últimos 12 meses. Acima de 6% é considerado bom para ações; acima de 8% para FIIs.',
    ms: 'Margem de Segurança — desconto do preço atual em relação ao preço justo calculado. Quanto maior, mais "barato" está o ativo em relação ao seu valor intrínseco.',
    score: SCORE_GLOSSARY,
    bazin:
      'Método Décio Bazin — define o Preço Teto como o dividendo médio anual dividido pela sua meta de yield, configurável por classe em Configurações (padrão: 6% ações BR, 10% FIIs, 4% ETFs). A média usa os anos-calendário completos disponíveis, excluindo o ano corrente. Comprar abaixo do teto garante um DY mínimo. Não se aplica a BDRs (avaliados por Graham/DCF).',
    dcf: 'Fluxo de Caixa Descontado simplificado — projeta o lucro por ação por 5 anos usando o crescimento de receita do ativo (8% a.a. quando o dado não está disponível ou é implausível), desconta a 13% a.a. e soma um valor terminal a P/L 15. Usado em BDRs e em ações sem histórico de dividendos.',
    rsi: 'Índice de Força Relativa (14 dias) — mede se o ativo subiu ou caiu rápido demais no curto prazo. Acima de 70 indica sobrecompra (risco de correção); abaixo de 30, sobrevenda (possível ponto de entrada). É sinal de timing, não de qualidade.',
    tendencia:
      'Comparação entre a média móvel curta e a longa do preço. Com histórico de 2 anos usa as médias de 50 e 200 dias; com histórico curto cai para 20 e 50 dias e a tela sinaliza isso — tendência de curto prazo é mais ruidosa.',
    roe: 'Retorno sobre o Patrimônio Líquido — quanto de lucro a empresa gera para cada R$ 1 de patrimônio dos acionistas. Acima de 15% a.a. é considerado bom. Não se aplica a FIIs nem ETFs.',
    de: 'Dívida / Patrimônio Líquido — quanto a empresa deve em relação ao próprio patrimônio. Abaixo de 100% é confortável; muito acima disso, o lucro fica sensível a juros.',
    consenso:
      'Média dos métodos de preço justo aplicáveis ao ativo (Bazin, Graham, DCF, valor patrimonial). A tela mostra quantos métodos entraram na conta: um consenso de um único método é bem menos confiável que de três.',
    data_years:
      'Quantos anos-calendário de proventos o sistema encontrou para o ativo. Menos de 3 anos torna o Bazin pouco confiável — o número aparece ao lado do veredito justamente para você poder descontar isso.',
    graham:
      'Fórmula Benjamin Graham — Preço Intrínseco = √(22,5 × LPA × VPA). Válido para empresas com P/L ≤ 15 e P/VP ≤ 1,5. Preço abaixo = potencial de valorização.',
    pvp: 'Preço / Valor Patrimonial — quanto se paga por cada R$ 1 de patrimônio. P/VP < 1 indica desconto (comum em FIIs atrativos); > 1 indica ágio.',
    lpa: 'Lucro Por Ação — lucro líquido da empresa dividido pelo número de ações em circulação. Quanto maior e mais consistente, melhor.',
    vpa: 'Valor Patrimonial por Ação — patrimônio líquido da empresa dividido pelo número de ações. Indica o "valor contábil" de cada ação.',
  };
}
