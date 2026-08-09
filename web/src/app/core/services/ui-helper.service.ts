import { Injectable } from '@angular/core';
import { AssetType, PortfolioSnapshot, Verdict } from '../models';

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
      us_stock: 'Ação EUA',
      crypto: 'Cripto',
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
      us_stock: 'flag',
      crypto: 'bitcoin',
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
      us_stock: 'var(--series-7)',
      crypto: 'var(--series-8)',
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
      acoes_int: 'Ações INT',
      fiis: 'FIIs',
      cripto: 'Cripto',
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
      acoes_int: 'globe',
      fiis: 'building-2',
      cripto: 'bitcoin',
    };
    return map[c] || 'circle';
  }

  categoryColor(c: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'text-blue-400',
      acoes_br: 'text-green-400',
      acoes_int: 'text-purple-400',
      fiis: 'text-orange-400',
      cripto: 'text-yellow-400',
    };
    return map[c] || 'text-muted';
  }

  categoryBarClass(c: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'bg-blue-400',
      acoes_br: 'bg-green-400',
      acoes_int: 'bg-purple-400',
      fiis: 'bg-orange-400',
      cripto: 'bg-yellow-400',
    };
    return map[c] || 'bg-muted';
  }

  categoryBgClass(c: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'bg-blue-500',
      acoes_br: 'bg-green-500',
      acoes_int: 'bg-purple-500',
      fiis: 'bg-orange-500',
      cripto: 'bg-yellow-500',
    };
    return map[c] || 'bg-muted';
  }

  categoryBarColor(c: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'rgba(59, 130, 246, 0.6)',
      acoes_br: 'rgba(34, 197, 94, 0.6)',
      acoes_int: 'rgba(168, 85, 247, 0.6)',
      fiis: 'rgba(251, 191, 36, 0.6)',
      cripto: 'rgba(249, 115, 22, 0.6)',
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
      crypto: 'Cripto',
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
      Cripto: 'bitcoin',
      Outros: 'circle-dot',
    };
    return map[s] || 'chart-bar';
  }

  alertIcon(kind: string): string {
    const map: Record<string, string> = {
      sell_target: 'trending-down',
      opportunity: 'trending-up',
      concentration: 'chart-pie',
    };
    return map[kind] || 'info';
  }

  portfolioSummary(positions: any[], totalPnl: number, totalPnlPct: number): string {
    const count = positions.length;
    const signal = totalPnl >= 0 ? 'lucro' : 'prejuízo';
    return `Você tem ${count} ${count === 1 ? 'posição' : 'posições'} com ${signal} de ${Math.abs(totalPnlPct).toFixed(2)}%.`;
  }

  minSnapshot(snapshots: PortfolioSnapshot[]): number {
    if (!snapshots.length) return 0;
    return Math.min(...snapshots.map(s => s.total_current));
  }

  maxSnapshot(snapshots: PortfolioSnapshot[]): number {
    if (!snapshots.length) return 0;
    return Math.max(...snapshots.map(s => s.total_current));
  }

  snapshotPath(
    snapshots: PortfolioSnapshot[],
    width: number,
    height: number,
    offsetX: number = 0,
    offsetY: number = 0
  ): string {
    if (!snapshots.length) return '';
    const values = snapshots.map(s => s.total_current);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const xStep = width / (values.length - 1 || 1);

    const points = values.map((v, i) => {
      const x = offsetX + i * xStep;
      const y = offsetY + height - ((v - min) / range) * height;
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  }

  snapshotAreaPath(
    snapshots: PortfolioSnapshot[],
    width: number,
    height: number,
    offsetX: number = 0,
    offsetY: number = 0
  ): string {
    if (!snapshots.length) return '';
    const values = snapshots.map(s => s.total_current);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const xStep = width / (values.length - 1 || 1);

    const points = values.map((v, i) => {
      const x = offsetX + i * xStep;
      const y = offsetY + height - ((v - min) / range) * height;
      return `${x},${y}`;
    });

    const bottomRight = `${offsetX + width},${offsetY + height}`;
    const bottomLeft = `${offsetX},${offsetY + height}`;

    return `M ${points[0]} L ${points.slice(1).join(' L ')} L ${bottomRight} L ${bottomLeft} Z`;
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

  scoreLabel(score: number): { text: string; cls: string } {
    if (score >= 75) return { text: 'Excelente entrada', cls: 'text-green-400' };
    if (score >= 60) return { text: 'Boa oportunidade', cls: 'text-accent' };
    if (score >= 40) return { text: 'Neutro', cls: 'text-yellow-400' };
    return { text: 'Evitar agora', cls: 'text-red-400' };
  }

  readonly glossary: Record<string, string> = {
    dy: 'Dividend Yield — percentual do preço atual pago em dividendos nos últimos 12 meses. Acima de 6% é considerado bom para ações; acima de 8% para FIIs.',
    ms: 'Margem de Segurança — desconto do preço atual em relação ao preço justo calculado. Quanto maior, mais "barato" está o ativo em relação ao seu valor intrínseco.',
    score:
      'Pontuação 0–100 calculada pelo sistema combinando valuation, histórico de dividendos e qualidade do ativo. Acima de 70 = oportunidade; 40–70 = neutro; abaixo de 40 = cuidado.',
    bazin:
      'Método Décio Bazin — define o Preço Teto como o dividendo anual dividido pela meta de yield: 6% (ações BR) ou 10% (FIIs). Comprar abaixo do teto garante um DY mínimo. Não se aplica a BDRs/ações internacionais (avaliadas por Graham/DCF).',
    graham:
      'Fórmula Benjamin Graham — Preço Intrínseco = √(22,5 × LPA × VPA). Válido para empresas com P/L ≤ 15 e P/VP ≤ 1,5. Preço abaixo = potencial de valorização.',
    pvp: 'Preço / Valor Patrimonial — quanto se paga por cada R$ 1 de patrimônio. P/VP < 1 indica desconto (comum em FIIs atrativos); > 1 indica ágio.',
    lpa: 'Lucro Por Ação — lucro líquido da empresa dividido pelo número de ações em circulação. Quanto maior e mais consistente, melhor.',
    vpa: 'Valor Patrimonial por Ação — patrimônio líquido da empresa dividido pelo número de ações. Indica o "valor contábil" de cada ação.',
  };
}
