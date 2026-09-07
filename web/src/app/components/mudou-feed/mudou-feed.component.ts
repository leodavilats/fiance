import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import {
  ActionKind,
  Alert,
  DashboardResponse,
  FiState,
  RecommendService,
  WhatsNewResponse,
} from '../../core';
import { InsightComponent } from '../insight/insight.component';

interface FeedItem {
  readonly title: string;
  readonly detail: string;
  readonly state: FiState;
  readonly actionLabel: string;
  readonly action: ActionKind | null;
  readonly ticker: string | null;
  readonly weight: number;
}

const FEED_LIMIT = 6;

/**
 * O feed do que mudou, que morava em `/hoje`.
 *
 * `Hoje` respondia "o que mudou e o que merece atenção", e isso é um feed, não um lugar — o
 * produto já sabia disso quando transformou `Atividade` em drawer. Com um mês no produto, o
 * "agora" é o mês, e o feed passa a viver dentro dele.
 *
 * Ele busca o próprio dado de propósito: o que sobrou de `/hoje` era um componente amarrado ao
 * `DashboardResponse` da tela, e desamarrá-lo é o que torna a distribuição possível sem levar a
 * tela inteira junto.
 */
@Component({
  selector: 'app-mudou-feed',
  standalone: true,
  imports: [CommonModule, InsightComponent],
  template: `
    @if (itens().length > 0) {
      <div>
        @for (item of itens(); track item.title; let first = $first) {
          <app-insight
            [title]="item.title"
            [detail]="item.detail"
            [state]="item.state"
            [actionLabel]="item.actionLabel"
            [divided]="!first"
            (action)="executar(item.action, item.ticker)"
          />
        }
      </div>
    } @else if (!carregando()) {
      <p class="fi-body text-ink-2 m-0 py-3">Nada mudou desde ontem.</p>
    }
  `,
})
export class MudouFeedComponent implements OnInit {
  private readonly svc = inject(RecommendService);
  private readonly router = inject(Router);

  readonly dados = signal<DashboardResponse | null>(null);
  readonly mudou = signal<WhatsNewResponse | null>(null);
  readonly carregando = signal(true);

  readonly diasDesde = computed(() => this.mudou()?.days_since ?? null);

  ngOnInit(): void {
    this.svc.dashboard().subscribe({
      next: res => {
        this.dados.set(res);
        this.carregando.set(false);
      },
      error: () => this.carregando.set(false),
    });

    this.svc.whatsNew().subscribe({
      next: res => this.mudou.set(res),
      error: () => this.mudou.set(null),
    });
  }

  readonly itens = computed<FeedItem[]>(() => {
    const d = this.dados();
    const items: FeedItem[] = [];

    for (const alert of d?.alerts ?? []) {
      items.push({
        title: alert.count > 1 ? `${alert.title} (${alert.count})` : alert.title,
        detail: alert.detail,
        state: this.estadoDoAlerta(alert),
        actionLabel: alert.action_label ?? '',
        action: alert.action,
        ticker: alert.ticker ?? null,
        weight: alert.severity === 'critical' ? 0 : alert.severity === 'warning' ? 1 : 3,
      });
    }

    for (const item of this.mudou()?.items ?? []) {
      if (item.kind === 'empty') continue;
      items.push({
        title: item.title,
        detail: item.detail,
        state: this.estadoDoQueMudou(item.severity),
        actionLabel: item.action_label ?? '',
        action: item.action,
        ticker: item.ticker,
        weight: item.severity === 'critical' ? 0 : item.severity === 'warning' ? 1 : 2,
      });
    }

    const vendas = d?.top_sells ?? [];
    if (vendas.length > 0) {
      items.push({
        title: `${vendas.length} ${vendas.length === 1 ? 'posição' : 'posições'} com sinal de venda`,
        detail: vendas.map(p => p.ticker).join(', '),
        state: 'attention',
        actionLabel: 'Ver patrimônio',
        action: 'rebalance',
        ticker: null,
        weight: 1,
      });
    }

    const meta = d?.summary.passive_income_goal;
    const progresso = d?.summary.passive_income_progress;
    if (meta && meta > 0 && progresso != null) {
      items.push({
        title: `Você está em ${progresso.toFixed(0)}% da sua meta de renda mensal`,
        detail: `R$ ${(d!.summary.monthly_dividends_estimate ?? 0).toFixed(0)} estimados de R$ ${meta.toFixed(0)}.`,
        state: progresso >= 100 ? 'favorable' : 'neutral',
        actionLabel: 'Ajustar meta',
        action: 'goals',
        ticker: null,
        weight: 4,
      });
    }

    return items.sort((a, b) => a.weight - b.weight).slice(0, FEED_LIMIT);
  });

  private estadoDoAlerta(alert: Alert): FiState {
    if (alert.severity === 'critical') return 'adverse';
    if (alert.severity === 'warning') return 'attention';
    return 'neutral';
  }

  private estadoDoQueMudou(severity: string): FiState {
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

  executar(action: ActionKind | null, ticker?: string | null): void {
    switch (action) {
      case 'analyze':
        this.router.navigate(ticker ? ['/ativo', ticker] : ['/patrimonio']);
        break;
      case 'sell':
        this.router.navigate(['/patrimonio']);
        break;
      case 'rebalance':
        this.router.navigate(['/patrimonio']);
        break;
      case 'goals':
        this.router.navigate(['/sobra/metas']);
        break;
      case 'fixed_income':
        this.router.navigate(['/patrimonio/editar']);
        break;
      case 'market':
      default:
        this.router.navigate(ticker ? ['/ativo', ticker] : ['/descobrir/oportunidades']);
    }
  }
}
