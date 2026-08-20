import { Injectable } from '@angular/core';
import { AssetType, Verdict } from '../models';
import {
  MIN_DATA_COMPLETENESS,
  SCORE_GLOSSARY,
  SCORE_NEUTRAL,
  SCORE_STRONG,
  ScoreBand,
  scoreBand,
} from '../score-ruler';

@Injectable({ providedIn: 'root' })
export class UiHelperService {
  formatTimestamp(ts: number): string {
    return new Date(ts * 1000).toLocaleString('pt-BR');
  }

  assetTypeLabel(t: AssetType | string): string {
    const map: Record<string, string> = {
      br_stock: 'Ação BR',
      bdr: 'BDR',
      fii: 'FII',
      etf: 'ETF',
      renda_fixa: 'Renda Fixa',
    };
    return map[t] || t;
  }

  assetTypeIcon(t: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'landmark',
      br_stock: 'trending-up',
      bdr: 'globe',
      fii: 'building-2',
      etf: 'layers',
    };
    return map[t] || 'circle';
  }

  // Cores categóricas fixas (não ciclam) — mesma cor sempre representa o mesmo tipo/segmento.
  assetTypeSeriesColor(t: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'var(--series-1)',
      br_stock: 'var(--series-2)',
      fii: 'var(--series-3)',
      bdr: 'var(--series-5)',
      etf: 'var(--series-8)',
    };
    return map[t] || 'var(--series-muted)';
  }

  sectorSeriesColor(sectorLabel: string): string {
    const map: Record<string, string> = {
      Financeiro: 'var(--series-1)',
      Tecnologia: 'var(--series-2)',
      Energia: 'var(--series-3)',
      'Consumo Cíclico': 'var(--series-4)',
      Saúde: 'var(--series-5)',
      Industrial: 'var(--series-6)',
      Imobiliário: 'var(--series-7)',
      'Consumo Básico': 'var(--series-8)',
      'Materiais Básicos': 'var(--series-9)',
      'Utilidades Públicas': 'var(--series-10)',
      Telecomunicações: 'var(--series-11)',
    };
    return map[sectorLabel] || 'var(--series-muted)';
  }

  categoryLabel(c: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'Renda Fixa',
      acoes_br: 'Ações BR',
      bdrs: 'BDRs',
      fiis: 'FIIs',
      etfs: 'ETFs',
      renda: 'Renda Fixa',
      trade: 'Ações BR',
      caixa: 'Renda Fixa',
      auto: 'Auto',
    };
    return map[c] || c;
  }

  categoryIcon(c: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'landmark',
      acoes_br: 'trending-up',
      bdrs: 'globe',
      fiis: 'building-2',
      etfs: 'layers',
    };
    return map[c] || 'circle';
  }

  categoryColor(c: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'text-blue-400',
      acoes_br: 'text-green-400',
      bdrs: 'text-purple-400',
      fiis: 'text-orange-400',
      etfs: 'text-yellow-400',
    };
    return map[c] || 'text-muted';
  }

  categoryBarClass(c: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'bg-blue-400',
      acoes_br: 'bg-green-400',
      bdrs: 'bg-purple-400',
      fiis: 'bg-orange-400',
      etfs: 'bg-yellow-400',
    };
    return map[c] || 'bg-muted';
  }

  categoryBgClass(c: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'bg-blue-500',
      acoes_br: 'bg-green-500',
      bdrs: 'bg-purple-500',
      fiis: 'bg-orange-500',
      etfs: 'bg-yellow-500',
    };
    return map[c] || 'bg-muted';
  }

  categoryBarColor(c: string): string {
    // Mantido em paridade com categoryBarClass/categoryBgClass/categoryColor
    // (fiis=laranja, etfs=amarelo) — fonte da verdade também usada pelo mobile.
    const map: Record<string, string> = {
      renda_fixa: 'rgba(59, 130, 246, 0.6)',
      acoes_br: 'rgba(34, 197, 94, 0.6)',
      bdrs: 'rgba(168, 85, 247, 0.6)',
      fiis: 'rgba(251, 146, 60, 0.6)',
      etfs: 'rgba(250, 204, 21, 0.6)',
    };
    return map[c] || 'rgba(148, 163, 184, 0.5)';
  }

  verdictClass(v: Verdict): string {
    const map: Record<Verdict, string> = {
      STRONG_BUY: 'verdict-strong-buy',
      BUY: 'verdict-buy',
      HOLD: 'verdict-hold',
      SELL: 'verdict-sell',
      STRONG_SELL: 'verdict-strong-sell',
      UNKNOWN: 'verdict-unknown',
    };
    return map[v] || 'verdict-unknown';
  }

  trendLabel(t: string): string {
    const map: Record<string, string> = {
      uptrend: '↗ Alta',
      downtrend: '↘ Baixa',
      sideways: '→ Lateral',
    };
    return map[t] || t;
  }

  rsiLabel(v: number | null): string {
    if (v == null) return '';
    if (v >= 70) return '(sobrecomprado)';
    if (v <= 30) return '(sobrevendido)';
    return '';
  }

  dyClass(dy: number | null): string {
    if (dy == null) return '';
    if (dy >= 8) return 'dy-high';
    if (dy >= 5) return 'dy-mid';
    return 'dy-low';
  }

  fmtNum(v: number | null): string {
    if (v == null) return '—';
    return v.toFixed(2);
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
      // Taxonomia da BRAPI (/quote/list) — diferente da usada pelo
      // yfinance acima, mapeada pras mesmas categorias em português.
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

  alertIcon(kind: string): string {
    const map: Record<string, string> = {
      sell_target: 'trending-down',
      opportunity: 'trending-up',
      concentration: 'chart-pie',
      rebalance: 'scale',
    };
    return map[kind] || 'info';
  }

  portfolioSummary(positions: any[], totalPnl: number, totalPnlPct: number): string {
    const count = positions.length;
    const signal = totalPnl >= 0 ? 'lucro' : 'prejuízo';
    return `Você tem ${count} ${count === 1 ? 'posição' : 'posições'} com ${signal} de ${Math.abs(totalPnlPct).toFixed(2)}%.`;
  }

  toNum(v: string | number | null): number | null {
    if (typeof v === 'number') return v;
    if (!v || v.trim() === '') return null;
    const parsed = parseFloat(v);
    return isNaN(parsed) ? null : parsed;
  }

  verdictFromLabel(label: string): Verdict {
    const map: Record<string, Verdict> = {
      'Compra Forte': 'STRONG_BUY',
      Compra: 'BUY',
      Manter: 'HOLD',
      Vender: 'SELL',
      'Venda Forte': 'STRONG_SELL',
    };
    return map[label] || 'UNKNOWN';
  }

  dipBarClass(score: number, max: number): string {
    const pct = (score / max) * 100;
    if (pct >= 75) return 'bg-accent';
    if (pct >= 50) return 'bg-accent/70';
    if (pct >= 25) return 'bg-accent/40';
    return 'bg-border';
  }

  dipVerdictClass(verdict: string): string {
    const map: Record<string, string> = {
      OPORTUNIDADE: 'verdict-oportunidade',
      NEUTRO: 'verdict-neutro',
      ARMADILHA: 'verdict-armadilha',
    };
    return map[verdict] || 'verdict-neutro';
  }

  /** Delegado à régua única (core/score-ruler.ts). */
  scoreLabel(score: number): ScoreBand {
    return scoreBand(score);
  }

  /**
   * Score com dado incompleto sai cinza, com o motivo — não colorido com a
   * nota. Antes não havia como saber se o 32 de um FII significava "ruim" ou
   * "não sei": a ausência de dado era codificada como número baixo.
   */
  scoreIsReliable(dataCompleteness: number | null | undefined): boolean {
    return (dataCompleteness ?? 1) >= MIN_DATA_COMPLETENESS;
  }

  scoreBandFor(score: number, dataCompleteness: number | null | undefined): ScoreBand {
    if (!this.scoreIsReliable(dataCompleteness)) {
      return { text: 'Dado insuficiente', cls: 'text-muted' };
    }
    return scoreBand(score);
  }

  scoreColorClass(score: number, dataCompleteness: number | null | undefined): string {
    if (!this.scoreIsReliable(dataCompleteness)) return 'text-muted';
    if (score >= SCORE_STRONG) return 'good';
    if (score >= SCORE_NEUTRAL) return 'warn';
    return 'text-muted';
  }

  dataCompletenessLabel(dataCompleteness: number | null | undefined): string {
    const value = dataCompleteness ?? 1;
    if (value >= 1) return '';
    return `${Math.round(value * 100)}% dos indicadores disponíveis`;
  }

  /**
   * Rótulo da base da tendência. Com histórico curto (plano gratuito da BRAPI
   * só devolve ranges curtos) a SMA200 não existe e a tendência é de curto
   * prazo — dizer isso é mais honesto que apresentar as duas como iguais.
   */
  trendBasisLabel(basis: string | null | undefined): string {
    const map: Record<string, string> = {
      long: 'médias de 50 e 200 dias',
      short: 'médias de 20 e 50 dias (histórico curto)',
      none: 'sem histórico suficiente',
    };
    return map[basis ?? 'none'] ?? '';
  }

  /** Proveniência do preço justo, ao lado de todo veredito. */
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
