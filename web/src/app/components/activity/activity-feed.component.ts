import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  DividendReceived,
  FiState,
  RecommendService,
  WhatsNewItem,
  WhatsNewResponse,
} from '../../core';
import { EmptyStateComponent } from '../empty-state/empty-state.component';
import { InsightComponent } from '../insight/insight.component';
import { SkeletonComponent } from '../skeleton/skeleton.component';

/** Um grupo de acontecimentos com o mesmo carimbo de tempo. */
interface ActivityGroup {
  readonly when: string;
  readonly note: string;
  readonly events: ActivityEvent[];
}

interface ActivityEvent {
  readonly title: string;
  readonly detail: string;
  readonly evidence: string;
  readonly state: FiState;
  readonly ticker: string | null;
}

const SEVERITY_STATE: Record<string, FiState> = {
  positive: 'favorable',
  warning: 'attention',
  critical: 'adverse',
  info: 'neutral',
};

const KIND_LABEL: Record<string, string> = {
  dividendo: 'Dividendo',
  jcp: 'JCP',
  rendimento: 'Rendimento',
  amortizacao: 'Amortização',
  outro: 'Provento',
};

/**
 * O histórico de acontecimentos relevantes — não um log técnico.
 *
 * Cada linha é um `Insight`: o que aconteceu, por que importa, o que sustenta.
 * Os eventos vêm agrupados por carimbo de tempo, e só existe carimbo quando o
 * dado tem data de verdade: o que o backend devolve como "mudou desde a sua
 * última visita" não tem hora por item, então aparece sob esse rótulo em vez de
 * ganhar um horário inventado (§57).
 *
 * Serve tanto ao drawer quanto à rota `/hoje/atividade` — mesma leitura, duas
 * embalagens.
 */
@Component({
  selector: 'app-activity-feed',
  standalone: true,
  imports: [CommonModule, EmptyStateComponent, InsightComponent, RouterLink, SkeletonComponent],
  template: `
    @if (loading()) {
      <div class="flex flex-col gap-5">
        <app-skeleton shape="title" />
        <app-skeleton shape="row" [count]="4" />
      </div>
    } @else if (groups().length === 0) {
      <app-empty-state
        icon="history"
        title="Nada aconteceu ainda"
        reason="A atividade reúne mudanças de veredito, proventos recebidos, desvios de meta e vencimentos — e nenhum desses eventos ocorreu desde que sua carteira foi cadastrada."
        nextStep="Assim que houver movimento de preço relevante ou um provento lançado, ele aparece aqui."
        actionLabel="Ver a carteira"
        actionRoute="/carteira"
      />
    } @else {
      @for (group of groups(); track group.when) {
        <section class="pt-5 first:pt-0">
          <div class="flex items-baseline justify-between gap-3">
            <p class="fi-eyebrow text-ink-3 m-0">{{ group.when }}</p>
            <p class="fi-caption text-ink-3 m-0">{{ group.note }}</p>
          </div>

          @for (event of group.events; track $index) {
            <app-insight
              [title]="event.title"
              [detail]="event.detail"
              [evidence]="event.evidence"
              [state]="event.state"
              [divided]="$index > 0"
            />
          }
        </section>
      }

      <p class="fi-caption text-ink-3 m-0 mt-6 pt-4 border-t border-hairline">
        A atividade cobre o que o fiance consegue observar: veredito, alocação, vencimento e
        proventos lançados.
        <a routerLink="/carteira/proventos" class="text-brand">Ver todos os proventos →</a>
      </p>
    }
  `,
})
export class ActivityFeedComponent implements OnInit {
  private readonly api = inject(RecommendService);

  readonly loading = signal(true);
  private readonly whatsNew = signal<WhatsNewResponse | null>(null);
  private readonly dividends = signal<DividendReceived[]>([]);

  ngOnInit(): void {
    let pending = 2;
    const done = () => {
      pending -= 1;
      if (pending === 0) this.loading.set(false);
    };

    this.api.whatsNew().subscribe({
      next: r => {
        this.whatsNew.set(r);
        done();
      },
      error: done,
    });

    this.api.getDividendsReceived().subscribe({
      next: r => {
        this.dividends.set(r.items ?? []);
        done();
      },
      error: done,
    });
  }

  readonly groups = computed<ActivityGroup[]>(() => {
    const groups: ActivityGroup[] = [];

    const news = this.whatsNew();
    const items = (news?.items ?? []).filter(i => i.kind !== 'empty');
    if (items.length > 0) {
      groups.push({
        when: 'Desde a sua última visita',
        note: this.sinceNote(news),
        events: items.map(i => this.fromWhatsNew(i)),
      });
    }

    for (const [month, received] of this.byMonth(this.dividends())) {
      const total = received.reduce((sum, d) => sum + d.amount, 0);
      groups.push({
        when: this.monthLabel(month),
        note: `${received.length} ${received.length === 1 ? 'lançamento' : 'lançamentos'}`,
        events: received.map(d => ({
          title: `${d.ticker} pagou ${this.money(d.amount)}`,
          detail: `${KIND_LABEL[d.kind] ?? 'Provento'} creditado em ${this.dayLabel(d.paid_at)}.`,
          evidence: d.note ?? `Total do mês: ${this.money(total)}.`,
          state: 'favorable' as FiState,
          ticker: d.ticker,
        })),
      });
    }

    return groups;
  });

  private fromWhatsNew(item: WhatsNewItem): ActivityEvent {
    return {
      title: item.title,
      detail: item.detail,
      evidence: item.ticker ? `Sobre ${item.ticker}.` : '',
      state: SEVERITY_STATE[item.severity] ?? 'neutral',
      ticker: item.ticker,
    };
  }

  private sinceNote(news: WhatsNewResponse | null): string {
    const days = news?.days_since;
    if (days == null) return 'primeira visita';
    if (days === 0) return 'hoje';
    return `há ${days} ${days === 1 ? 'dia' : 'dias'}`;
  }

  /** Agrupa por `AAAA-MM`, do mais recente para o mais antigo. */
  private byMonth(items: DividendReceived[]): [string, DividendReceived[]][] {
    const map = new Map<string, DividendReceived[]>();
    for (const d of items) {
      const month = (d.paid_at ?? '').slice(0, 7);
      if (month.length !== 7) continue;
      const bucket = map.get(month);
      if (bucket) bucket.push(d);
      else map.set(month, [d]);
    }
    return [...map.entries()]
      .sort((a, b) => b[0].localeCompare(a[0]))
      .map(([month, list]) => [month, list.sort((a, b) => b.paid_at.localeCompare(a.paid_at))]);
  }

  private monthLabel(month: string): string {
    const [year, m] = month.split('-');
    const date = new Date(Number(year), Number(m) - 1, 1);
    const label = date.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
    return label.charAt(0).toUpperCase() + label.slice(1);
  }

  private dayLabel(iso: string): string {
    const date = new Date(`${iso}T12:00:00`);
    if (Number.isNaN(date.getTime())) return iso;
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
  }

  private money(value: number): string {
    return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }
}
