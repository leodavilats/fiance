import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  CashEntry,
  CashMonth,
  CashflowService,
  Debt,
  mesCorrente,
  nomeDoMes,
  fiCategoriasDeDespesa,
  fiCategoriasDeEntrada,
} from '../../core';
import { ChangesFeedComponent } from '../changes-feed/changes-feed.component';
import { PageHeaderComponent } from '../page-header/page-header.component';
import { SkeletonComponent } from '../skeleton/skeleton.component';

interface LinhaDoMes {
  readonly entry: CashEntry;
  readonly futura: boolean;
}

@Component({
  selector: 'app-month',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    LucideAngularModule,
    ChangesFeedComponent,
    PageHeaderComponent,
    SkeletonComponent,
  ],
  template: `
    <app-page-header title="Mês" question="Como estou agora, e o que exige atenção?">
      @if (mesesDisponiveis().length > 1) {
        <div class="field mt-3 max-w-[16rem]">
          <label class="field-label" for="mes-escolhido">Mês</label>
          <select
            id="mes-escolhido"
            class="input"
            [value]="mesEscolhido()"
            (change)="escolherMes($any($event.target).value)"
          >
            @for (m of mesesDisponiveis(); track m) {
              <option [value]="m">{{ nome(m) }}</option>
            }
          </select>
        </div>
      }
    </app-page-header>

    @if (carregando()) {
      <app-skeleton shape="metric" />
    } @else if (mes(); as m) {
      @if (semLancamento()) {
        <div class="notice notice-brand">
          <lucide-icon name="circle-alert" size="18" aria-hidden="true"></lucide-icon>
          <div>
            <p class="fi-label m-0">Seu mês ainda não tem nada lançado</p>
            <p class="fi-body m-0 mt-1">
              Comece pelo que se repete: o dia e o valor que você recebe, e os dois ou três maiores
              gastos fixos. Com isso a sobra do mês já sai, e ela é o que decide o próximo aporte.
            </p>
            <a routerLink="/mes/lancar" class="btn-primary no-underline mt-3">
              <lucide-icon name="plus" size="16" aria-hidden="true"></lucide-icon>
              Lançar o primeiro mês
            </a>
          </div>
        </div>
      } @else {
        <section class="fi-block">
          <p class="fi-eyebrow text-ink-3 m-0">
            {{ ehMesCorrente() ? 'Livre agora' : 'Sobrou em ' + nome(m.month) }}
          </p>
          <p class="fi-money-xl text-ink m-0 mt-1">{{ reais(m.free_now) }}</p>

          <dl class="flex flex-wrap gap-x-10 gap-y-4 m-0 mt-5">
            <div>
              <dt class="fi-eyebrow text-ink-3">Entrou</dt>
              <dd class="fi-metric-sm text-ink m-0 mt-1">{{ reais(m.received) }}</dd>
            </div>
            <div>
              <dt class="fi-eyebrow text-ink-3">Saiu</dt>
              <dd class="fi-metric-sm text-ink m-0 mt-1">{{ reais(m.paid) }}</dd>
            </div>
            <div>
              <dt class="fi-eyebrow text-ink-3">Comprometido</dt>
              <dd class="fi-metric-sm text-ink m-0 mt-1">{{ reais(m.committed) }}</dd>
            </div>
          </dl>

          <p class="fi-body text-ink-2 m-0 mt-5 pt-4 border-t border-hairline max-w-reading">
            @if (m.has_range) {
              Descontando o que ainda deve sair, a sobra parte de
              <strong class="fi-num">{{ reais(m.surplus_low) }}</strong
              >.
            } @else {
              Sem mês fechado ainda não há como estimar o que falta sair, então a sobra é o próprio
              livre.
            }
            <a routerLink="/sobra" class="btn-link">decidir o que fazer com ela</a>
          </p>
        </section>

        <section class="fi-block">
          <p class="fi-eyebrow text-ink-3 m-0">O que mudou</p>
          <app-changes-feed />
        </section>

        @if (atencao().length > 0) {
          <section class="fi-block">
            <p class="fi-eyebrow text-ink-3 m-0">Exige atenção · {{ atencao().length }}</p>
            <ul class="list-none m-0 mt-3 p-0 flex flex-col gap-3">
              @for (d of atencao(); track d.id) {
                <li class="flex items-baseline justify-between gap-4 flex-wrap">
                  <span class="fi-body text-ink">
                    {{ d.description }}: <span class="fi-num">{{ reais(d.balance) }}</span> a
                    <span class="fi-num">{{ d.monthly_rate }}%</span> ao mês
                  </span>
                  <a routerLink="/mes/dividas" class="btn-link">Ver a dívida</a>
                </li>
              }
            </ul>
          </section>
        }

        @if (m.due.length > 0) {
          <section class="fi-block">
            <p class="fi-eyebrow text-ink-3 m-0">A vencer · {{ m.due.length }}</p>
            <div class="overflow-x-auto mt-3">
              <table class="data-table">
                <caption class="sr-only">
                  Contas com vencimento neste mês que ainda não foram pagas
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Dia</th>
                    <th scope="col">Conta</th>
                    <th scope="col" class="num">Valor</th>
                    <th scope="col"><span class="sr-only">Ação</span></th>
                  </tr>
                </thead>
                <tbody>
                  @for (conta of m.due; track conta.id) {
                    <tr>
                      <td class="num">{{ dia(conta.due_on) }}</td>
                      <td class="text-ink">{{ conta.description }}</td>
                      <td class="num">{{ reais(conta.amount) }}</td>
                      <td>
                        <button
                          type="button"
                          class="btn-secondary compact-btn"
                          (click)="pagar(conta.id)"
                          [disabled]="pagando() === conta.id"
                          [attr.title]="pagando() === conta.id ? 'Registrando o pagamento' : null"
                        >
                          {{ pagando() === conta.id ? 'Marcando…' : 'Marcar como paga' }}
                        </button>
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          </section>
        }

        <section class="fi-block">
          <div class="flex items-baseline justify-between gap-4 flex-wrap">
            <p class="fi-eyebrow text-ink-3 m-0">O mês</p>
            <a routerLink="/mes/lancar" class="btn-link">Lançar</a>
          </div>

          <div class="overflow-x-auto mt-3">
            <table class="data-table">
              <caption class="sr-only">
                Movimentos do mês em ordem de data, com o dia de hoje marcado
              </caption>
              <thead>
                <tr>
                  <th scope="col">Dia</th>
                  <th scope="col">Movimento</th>
                  <th scope="col">Categoria</th>
                  <th scope="col" class="num">Valor</th>
                </tr>
              </thead>
              <tbody>
                @if (linhas().length === 0) {
                  <tr>
                    <td colspan="4" class="text-ink-2">
                      Nada lançado em {{ nome(m.month) }}.
                      @if (mesesDisponiveis().length > 1) {
                        Você tem lançamentos em outros meses — troque no seletor acima.
                      }
                    </td>
                  </tr>
                }
                @for (linha of linhas(); track linha.entry.id + linha.entry.due_on) {
                  <tr>
                    <td class="num">{{ dia(linha.entry.paid_on ?? linha.entry.due_on) }}</td>
                    <td class="text-ink">
                      {{ linha.entry.description }}
                      @if (linha.futura) {
                        <span class="fi-caption text-ink-3">· a vencer</span>
                      }
                      @if (linha.entry.derived) {
                        <span class="fi-caption text-ink-3">· do seu razão</span>
                      }
                    </td>
                    <td class="text-ink-2">{{ rotuloDaCategoria(linha.entry) }}</td>
                    <td
                      class="num"
                      [class.text-up]="linha.entry.kind === 'income'"
                      [class.text-down]="linha.entry.kind === 'expense'"
                    >
                      {{ linha.entry.kind === 'income' ? '+' : '−' }}{{ reais(linha.entry.amount) }}
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </section>
      }
    }
  `,
})
export class MonthComponent implements OnInit {
  private readonly api = inject(CashflowService);
  private readonly rota = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly nome = nomeDoMes;

  readonly mes = signal<CashMonth | null>(null);
  readonly mesEscolhido = signal<string>(mesCorrente());
  readonly entradas = signal<CashEntry[]>([]);
  readonly dividas = signal<Debt[]>([]);
  readonly carregando = signal(true);
  readonly pagando = signal<number | null>(null);

  readonly semLancamento = computed(() => this.entradas().every(e => e.derived));

  readonly atencao = computed(() => this.dividas().filter(d => d.class === 'expensive'));

  readonly ehMesCorrente = computed(() => this.mesEscolhido() === mesCorrente());

  /** Os meses que a pessoa tem, mais o corrente. Nada de faixa inventada. */
  readonly mesesDisponiveis = computed(() => {
    const meses = new Set<string>([mesCorrente()]);
    for (const e of this.entradas()) meses.add((e.paid_on ?? e.due_on).slice(0, 7));
    return [...meses].sort().reverse();
  });

  readonly linhas = computed<LinhaDoMes[]>(() => {
    const mes = this.mes()?.month;
    if (!mes) return [];

    return this.entradas()
      .filter(e => (e.paid_on ?? e.due_on).startsWith(mes))
      .map(e => ({ entry: e, futura: e.paid_on === null }))
      .sort((a, b) =>
        (a.entry.paid_on ?? a.entry.due_on).localeCompare(b.entry.paid_on ?? b.entry.due_on)
      );
  });

  ngOnInit(): void {
    this.rota.queryParamMap.subscribe(params => {
      this.mesEscolhido.set(params.get('mes') ?? mesCorrente());
      this.carregar();
    });
  }

  escolherMes(mes: string): void {
    void this.router.navigate([], {
      relativeTo: this.rota,
      queryParams: { mes: mes === mesCorrente() ? null : mes },
      queryParamsHandling: 'merge',
    });
  }

  carregar(): void {
    this.carregando.set(true);

    this.api.month(this.mesEscolhido()).subscribe({
      next: m => {
        this.mes.set(m);
        this.carregando.set(false);
      },
      error: () => this.carregando.set(false),
    });

    this.api.entries().subscribe({ next: e => this.entradas.set(e) });
    this.api.debts().subscribe({ next: d => this.dividas.set(d) });
  }

  pagar(entryId: number | null): void {
    if (entryId === null) return;

    this.pagando.set(entryId);
    this.api.markPaid(entryId).subscribe({
      next: () => {
        this.pagando.set(null);
        this.carregar();
      },
      error: () => this.pagando.set(null),
    });
  }

  rotuloDaCategoria(entry: CashEntry): string {
    const mapa = entry.kind === 'income' ? fiCategoriasDeEntrada : fiCategoriasDeDespesa;
    return mapa[entry.category]?.label ?? entry.category;
  }

  dia(data: string): string {
    return data.slice(8, 10);
  }

  reais(valor: number): string {
    return valor.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
    });
  }
}
