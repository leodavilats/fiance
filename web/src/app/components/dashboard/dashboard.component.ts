import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  ActionKind,
  Alert,
  DashboardResponse,
  FiState,
  LoadingService,
  Opportunity,
  RecommendService,
  UiHelperService,
  WhatsNewResponse,
  fiBandFor,
  fiHealthBands,
} from '../../core';
import { InsightComponent } from '../insight/insight.component';
import { ScoreRulerComponent } from '../score-ruler/score-ruler.component';

interface FeedItem {
  readonly title: string;
  readonly detail: string;
  readonly state: FiState;
  readonly actionLabel: string;
  readonly action: ActionKind | null;
  readonly ticker: string | null;
  readonly weight: number;
}

interface AllocationGap {
  readonly label: string;
  readonly currentPct: number;
  readonly targetPct: number;
  readonly absDelta: number;
  readonly below: boolean;
}

const MIN_POSITIONS_FOR_HEALTH = 4;
const MIN_GAP_PP = 2;
const FEED_LIMIT = 6;
const TOP_BUYS_LIMIT = 3;

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink, ScoreRulerComponent, InsightComponent],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private readonly svc = inject(RecommendService);
  private readonly router = inject(Router);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  readonly data = signal<DashboardResponse | null>(null);
  readonly whatsNew = signal<WhatsNewResponse | null>(null);
  readonly isInitialLoad = signal(true);
  readonly errored = signal(false);

  readonly healthBands = fiHealthBands;

  ngOnInit(): void {
    this.loadDashboard();
  }

  loadDashboard(): void {
    this.errored.set(false);
    this.svc.dashboard().subscribe({
      next: res => {
        this.data.set(res);
        this.isInitialLoad.set(false);
      },
      error: () => {
        this.errored.set(true);
        this.isInitialLoad.set(false);
      },
    });

    this.svc.whatsNew().subscribe({
      next: res => this.whatsNew.set(res),
      error: () => this.whatsNew.set(null),
    });
  }

  readonly isEmptyPortfolio = computed(() => {
    const d = this.data();
    if (!d) return false;
    return d.summary.positions_count === 0 && d.summary.total_current === 0;
  });

  readonly absPnl = computed(() => Math.abs(this.data()?.summary.total_pnl ?? 0));

  pnlDirectionClass(): string {
    const pnl = this.data()?.summary.total_pnl ?? 0;
    if (pnl > 0) return 'text-up';
    if (pnl < 0) return 'text-down';
    return 'text-ink-2';
  }

  readonly healthReliability = computed(() => {
    const count = this.data()?.summary.positions_count ?? 0;
    return count >= MIN_POSITIONS_FOR_HEALTH ? 1 : 0;
  });

  readonly healthVerdict = computed(() => {
    const h = this.data()?.health;
    if (!h) return '';
    if (this.healthReliability() === 0) {
      return 'Sua carteira ainda é pequena para uma leitura de risco';
    }
    const band = fiBandFor(h.score, fiHealthBands);
    switch (band.id) {
      case 'healthy':
        return 'Carteira saudável';
      case 'ok':
        return 'Carteira em ordem, com pontos de atenção';
      case 'watch':
        return 'Sua carteira merece atenção';
      default:
        return 'Sua carteira precisa de ajustes';
    }
  });

  readonly healthReasons = computed<string[]>(() => {
    const d = this.data();
    const h = d?.health;
    if (!h) return [];

    if (this.healthReliability() === 0) {
      return [
        `Com ${d!.summary.positions_count} ${d!.summary.positions_count === 1 ? 'ativo' : 'ativos'}, concentração e diversificação ainda não dizem muito.`,
      ];
    }

    const reasons: string[] = [];

    if (h.top_position_ticker && h.top_position_pct != null && h.top_position_pct >= 15) {
      reasons.push(
        `${h.top_position_ticker} concentra ${h.top_position_pct.toFixed(1)}% da carteira.`
      );
    }
    if (h.top_sector && h.top_sector_pct != null && h.top_sector_pct >= 40) {
      reasons.push(
        `${this.ui.translateSector(h.top_sector)} responde por ${h.top_sector_pct.toFixed(1)}% das ações e BDRs.`
      );
    }

    for (const warning of h.warnings ?? []) {
      if (reasons.length >= 3) break;
      if (!reasons.includes(warning)) reasons.push(warning);
    }

    if (reasons.length === 0) {
      reasons.push('Nenhum ponto de concentração ou risco relevante identificado.');
    }
    return reasons.slice(0, 3);
  });

  readonly feed = computed<FeedItem[]>(() => {
    const d = this.data();
    const items: FeedItem[] = [];

    for (const alert of d?.alerts ?? []) {
      items.push({
        title: alert.count > 1 ? `${alert.title} (${alert.count})` : alert.title,
        detail: alert.detail,
        state: this.alertState(alert),
        actionLabel: alert.action_label ?? '',
        action: alert.action,
        ticker: alert.ticker ?? null,
        weight: alert.severity === 'critical' ? 0 : alert.severity === 'warning' ? 1 : 3,
      });
    }

    for (const item of this.whatsNew()?.items ?? []) {
      if (item.kind === 'empty') continue;
      items.push({
        title: item.title,
        detail: item.detail,
        state: this.whatsNewState(item.severity),
        actionLabel: item.action_label ?? '',
        action: item.action,
        ticker: item.ticker,
        weight: item.severity === 'critical' ? 0 : item.severity === 'warning' ? 1 : 2,
      });
    }

    const sells = d?.top_sells ?? [];
    if (sells.length > 0) {
      items.push({
        title: `${sells.length} ${sells.length === 1 ? 'posição' : 'posições'} com sinal de venda`,
        detail: sells.map(p => p.ticker).join(', '),
        state: 'attention',
        actionLabel: 'Ver estratégia',
        action: 'rebalance',
        ticker: null,
        weight: 1,
      });
    }

    const goal = d?.summary.passive_income_goal;
    const progress = d?.summary.passive_income_progress;
    if (goal && goal > 0 && progress != null) {
      items.push({
        title: `Você está em ${progress.toFixed(0)}% da sua meta de renda mensal`,
        detail: `R$ ${(d!.summary.monthly_dividends_estimate ?? 0).toFixed(0)} estimados de R$ ${goal.toFixed(0)}.`,
        state: progress >= 100 ? 'favorable' : 'neutral',
        actionLabel: 'Ajustar meta',
        action: 'goals',
        ticker: null,
        weight: 4,
      });
    }

    return items.sort((a, b) => a.weight - b.weight).slice(0, FEED_LIMIT);
  });

  private alertState(alert: Alert): FiState {
    if (alert.severity === 'critical') return 'adverse';
    if (alert.severity === 'warning') return 'attention';
    return 'neutral';
  }

  private whatsNewState(severity: string): FiState {
    switch (severity) {
      case 'positive':
        return 'favorable';
      case 'warning':
        return 'attention';
      case 'critical':
        return 'adverse';
      default:
        return 'neutral';
    }
  }

  readonly biggestGap = computed<AllocationGap | null>(() => {
    const allocations = this.data()?.allocations ?? [];
    const candidates = allocations
      .filter(a => a.target_pct != null && a.delta_pct != null)
      .map(a => ({
        label: this.ui.categoryLabel(a.category),
        currentPct: a.current_pct,
        targetPct: a.target_pct as number,
        absDelta: Math.abs(a.delta_pct as number),
        below: (a.delta_pct as number) < 0,
      }))
      .filter(a => a.absDelta >= MIN_GAP_PP)
      .sort((a, b) => b.absDelta - a.absDelta);

    return candidates[0] ?? null;
  });

  readonly topBuys = computed(() => (this.data()?.top_buys ?? []).slice(0, TOP_BUYS_LIMIT));

  opportunityReason(opp: Opportunity): string {
    const parts: string[] = [];
    if (opp.margin_of_safety != null) {
      const pct = Math.round(opp.margin_of_safety * 100);
      if (pct > 0) parts.push(`${pct}% abaixo do preço justo estimado`);
    }
    if (opp.dividend_yield != null && opp.dividend_yield > 0) {
      parts.push(`DY de ${opp.dividend_yield.toFixed(1)}%`);
    }
    if (parts.length === 0) return opp.name || opp.ticker;
    return parts.join(' · ');
  }

  runAction(action: ActionKind | null, ticker?: string | null): void {
    switch (action) {
      case 'analyze':
        this.router.navigate(ticker ? ['/ativo', ticker] : ['/carteira']);
        break;
      case 'sell':
        this.router.navigate(['/carteira']);
        break;
      case 'rebalance':
        this.router.navigate(['/estrategia']);
        break;
      case 'goals':
        this.router.navigate(['/estrategia/metas']);
        break;
      case 'fixed_income':
        this.router.navigate(['/carteira/editar']);
        break;
      case 'market':
      default:
        this.router.navigate(ticker ? ['/ativo', ticker] : ['/descobrir/oportunidades']);
    }
  }

  freshnessLabel(): string {
    const freshness = this.data()?.freshness;
    if (!freshness) return '';

    const age = freshness.market_data_age_seconds;
    if (age == null) return 'cotações sem carimbo de tempo';
    if (age < 120) return 'cotações de agora';
    if (age < 3600) return `cotações de ${Math.round(age / 60)} min atrás`;
    return `cotações de ${Math.round(age / 3600)} h atrás`;
  }

  ratesSourceLabel(): string {
    const source = this.data()?.freshness?.rates_source;
    if (!source) return '';
    return source === 'bcb' ? 'CDI e Selic do Banco Central' : 'CDI e Selic estimados';
  }
}
