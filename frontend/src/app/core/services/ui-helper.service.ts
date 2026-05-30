import { Injectable } from '@angular/core';
import { AssetType, PortfolioSnapshot, Verdict } from '../models';

@Injectable({ providedIn: 'root' })
export class UiHelperService {
  formatTimestamp(ts: number): string {
    return new Date(ts * 1000).toLocaleString('pt-BR');
  }

  assetTypeLabel(t: AssetType): string {
    const map: Record<AssetType, string> = {
      br_stock: 'Ação BR',
      fii: 'FII',
      us_stock: 'Ação EUA',
      crypto: 'Cripto',
    };
    return map[t] || t;
  }

  categoryLabel(c: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'Renda Fixa',
      acoes_br: 'Ações BR',
      acoes_int: 'Ações INT',
      fiis: 'FIIs',
      cripto: 'Cripto',
      // compatibilidade legada
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
      technology: 'Tecnologia',
      finance: 'Financeiro',
      healthcare: 'Saúde',
      energy: 'Energia',
      utilities: 'Utilidades Públicas',
      'consumer-discretionary': 'Consumo Discricionário',
      'consumer-staples': 'Consumo Básico',
      industrials: 'Industrial',
      materials: 'Materiais',
      'real-estate': 'Imobiliário',
      telecommunications: 'Telecom',
      crypto: 'Cripto',
    };
    return map[s] || s;
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

    // Criar path de área: linha + fechar pelo fundo
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
}
