import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { CashflowService, Surplus, nomeDoMes } from '../../core';
import { HelpTooltipComponent } from '../help-tooltip/help-tooltip.component';
import { PageHeaderComponent } from '../page-header/page-header.component';
import { SkeletonComponent } from '../skeleton/skeleton.component';
import { SectionComponent } from '../section/section.component';

@Component({
  selector: 'app-surplus',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    LucideAngularModule,
    PageHeaderComponent,
    HelpTooltipComponent,
    SkeletonComponent,
    SectionComponent,
  ],
  template: `
    <app-page-header
      title="Sobra"
      question="O que eu faço com o que sobrou?"
      [scope]="dados() ? nome(dados()!.month.month) : ''"
    />

    @if (carregando()) {
      <app-skeleton shape="metric" />
    } @else if (erro()) {
      <div class="notice notice-adverse">
        <lucide-icon name="circle-alert" size="18" aria-hidden="true"></lucide-icon>
        <div>
          <p class="fi-label m-0">Não foi possível ler o seu mês</p>
          <p class="fi-body m-0 mt-1">{{ erro() }}</p>
          <button type="button" class="btn-secondary compact-btn mt-3" (click)="carregar()">
            Tentar de novo
          </button>
        </div>
      </div>
    } @else if (dados(); as d) {
      @if (!d.has_cash) {
        <div class="notice notice-brand">
          <lucide-icon name="circle-alert" size="18" aria-hidden="true"></lucide-icon>
          <div>
            <p class="fi-label m-0">Sem lançamento de caixa, não há sobra para derivar</p>
            <p class="fi-body m-0 mt-1">
              A ordem abaixo precisa saber quanto entrou e quanto saiu no mês. Lançar o mês é o que
              substitui o palpite — enquanto isso não existir, esta tela não tem como responder.
            </p>
            <a routerLink="/mes/lancar" class="btn-primary no-underline mt-3">
              <lucide-icon name="plus" size="16" aria-hidden="true"></lucide-icon>
              Lançar o mês
            </a>
          </div>
        </div>
      } @else {
        <section class="fi-block">
          <p class="fi-eyebrow text-ink-3 m-0">
            {{ d.month.has_range ? 'Sobra, no piso' : 'Sobra' }}
          </p>
          <p class="fi-money-xl text-ink m-0 mt-1">{{ reais(d.month.surplus_low) }}</p>

          @if (d.month.has_range) {
            <p class="fi-body text-ink-2 m-0 mt-2">
              É o piso — até <span class="fi-num">{{ reais(d.month.surplus_high) }}</span> se o mês
              fechar como o mais barato dos últimos {{ d.month.estimate.base_months.length }} meses.
            </p>
          } @else {
            <p class="fi-body text-ink-2 m-0 mt-2">
              Sem mês fechado ainda não há como estimar o que falta sair, então este número é o que
              já está livre — não uma projeção.
            </p>
          }

          <dl class="flex flex-wrap gap-x-10 gap-y-4 m-0 mt-5 pt-4 border-t border-hairline">
            <div>
              <dt class="fi-eyebrow text-ink-3">Livre agora</dt>
              <dd class="fi-metric-sm text-ink m-0 mt-1">{{ reais(d.month.free_now) }}</dd>
            </div>
            @if (d.month.has_range) {
              <div>
                <dt class="fi-eyebrow text-ink-3">Ainda deve sair</dt>
                <dd class="fi-metric-sm text-ink m-0 mt-1">
                  {{ reais(d.month.estimate.remaining_high) }}
                </dd>
              </div>
            }
          </dl>

          <details class="mt-4">
            <summary class="btn-quiet btn-explain">Como esta faixa é calculada</summary>
            <div class="fi-body text-ink-2 mt-2 max-w-reading">
              @if (d.month.has_range) {
                <p class="m-0">
                  O gasto variável dos meses fechados
                  <span class="fi-num">{{ d.month.estimate.base_months.join(', ') }}</span>
                  ficou entre
                  <span class="fi-num">{{ reais(d.month.estimate.expected_low) }}</span> e
                  <span class="fi-num">{{ reais(d.month.estimate.expected_high) }}</span
                  >. Deste mês já saíram
                  <span class="fi-num">{{ reais(d.month.estimate.spent_so_far) }}</span
                  >, então falta sair entre
                  <span class="fi-num">{{ reais(d.month.estimate.remaining_low) }}</span> e
                  <span class="fi-num">{{ reais(d.month.estimate.remaining_high) }}</span
                  >.
                </p>
                <p class="m-0 mt-2">
                  A ordem decide sobre o <strong>piso</strong>: comprar cota com dinheiro que talvez
                  não chegue custa vender no prejuízo ou atrasar uma conta, enquanto aportar menos
                  custa um mês de rendimento. Os dois erros não têm o mesmo preço.
                </p>
              } @else {
                <p class="m-0">
                  A faixa sai do gasto variável dos seus meses fechados, e você ainda não tem
                  nenhum. Enquanto isso, o número é o que já está livre — tratar a ausência de
                  histórico como "nada mais vai sair" daria uma sobra otimista justo para quem
                  acabou de começar.
                </p>
              }
            </div>
          </details>
        </section>

        <app-section
          title="A ordem"
          tone="title"
          hint="Cada passo consome parte da sobra, na ordem em que vale a pena gastá-la."
        >
          <app-help-tooltip
            sectionActions
            term="a ordem"
            text="Cada passo consome parte da sobra e diz o que o derrubaria. Dívida cara vem
                  antes de aporte porque é aritmética de taxa: enquanto o juro da dívida for
                  maior que o retorno da sua carteira, quitar rende mais que investir. Dívida
                  não é valor mobiliário, então isso não é recomendação de investimento."
          />

          @if (d.cascade.steps.length === 0) {
            <div class="notice notice-attention mt-4">
              <lucide-icon name="circle-alert" size="18" aria-hidden="true"></lucide-icon>
              <div>
                <p class="fi-label m-0">O mês fecha sem sobra</p>
                <p class="fi-body m-0 mt-1">
                  Com o que está lançado, não há valor a destinar. A linha do tempo do mês mostra o
                  que pesou.
                </p>
                <a routerLink="/mes" class="btn-secondary compact-btn no-underline mt-3"
                  >Ver o mês</a
                >
              </div>
            </div>
          } @else {
            <ol class="list-none m-0 mt-3 p-0 divide-y divide-hairline">
              @for (passo of d.cascade.steps; track passo.order) {
                <li class="flex items-baseline gap-4 py-4">
                  <span class="fi-metric text-ink-3 shrink-0" aria-hidden="true">
                    {{ passo.order }}
                  </span>

                  <div class="flex-1 min-w-0">
                    <div class="flex items-baseline justify-between gap-4 flex-wrap">
                      <p class="fi-title text-ink m-0">{{ rotuloDoPasso(passo.type) }}</p>
                      <p class="fi-metric text-ink m-0">{{ reais(passo.amount) }}</p>
                    </div>

                    <p class="fi-verdict-sm text-ink m-0 mt-1 max-w-reading">{{ passo.reason }}</p>

                    <div class="flex items-baseline gap-5 flex-wrap mt-2">
                      @if (passo.type === 'debt') {
                        <a routerLink="/mes/dividas" class="btn-link">Ver a dívida</a>
                      }
                      @if (passo.type === 'contribution') {
                        <a routerLink="/sobra/aporte" class="btn-link">Ver onde aportar</a>
                      }
                      @if (passo.falsifier) {
                        <details>
                          <summary class="btn-quiet btn-explain">O que derrubaria isto</summary>
                          <p class="fi-body text-ink-2 m-0 mt-2 max-w-reading">
                            {{ passo.falsifier }}
                          </p>
                        </details>
                      }
                    </div>
                  </div>
                </li>
              }
            </ol>

            @if (!temAporte()) {
              <p class="fi-body text-ink-2 m-0 mt-4 max-w-reading">
                Este mês a ordem termina sem aporte, e isso é a resposta — não uma falha. Enquanto a
                dívida custar mais que a sua carteira rende, quitar é o melhor uso do dinheiro.
              </p>
            }
          }
        </app-section>
      }
    }
  `,
})
export class SurplusComponent implements OnInit {
  readonly nome = nomeDoMes;

  private readonly api = inject(CashflowService);

  readonly dados = signal<Surplus | null>(null);
  readonly carregando = signal(true);
  readonly erro = signal('');

  readonly temAporte = computed(
    () => this.dados()?.cascade.steps.some(p => p.type === 'contribution') ?? false
  );

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.carregando.set(true);
    this.erro.set('');

    this.api.surplus().subscribe({
      next: d => {
        this.dados.set(d);
        this.carregando.set(false);
      },
      error: () => {
        this.erro.set('Tente de novo em alguns instantes.');
        this.carregando.set(false);
      },
    });
  }

  rotuloDoPasso(tipo: string): string {
    if (tipo === 'debt') return 'Dívida';
    if (tipo === 'reserve') return 'Reserva';
    return 'Aporte';
  }

  reais(valor: number): string {
    return valor.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
    });
  }
}
