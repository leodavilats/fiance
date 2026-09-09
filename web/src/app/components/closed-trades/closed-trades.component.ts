import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { CarteiraStore, UiHelperService } from '../../core';
import { AsyncStateComponent } from '../async-state/async-state.component';
import { HelpTooltipComponent } from '../help-tooltip/help-tooltip.component';
import { PageHeaderComponent } from '../page-header/page-header.component';

@Component({
  selector: 'app-closed-trades',
  standalone: true,
  imports: [
    PageHeaderComponent,
    CommonModule,
    LucideAngularModule,
    HelpTooltipComponent,
    AsyncStateComponent,
  ],
  template: `
    <app-page-header
      title="Operações encerradas"
      question="O que eu já vendi, com quanto de lucro e quanto de imposto?"
    />

    <app-async-state
      [loading]="carregando()"
      [error]="erroDeCarga()"
      [empty]="vazio()"
      loadingShape="row"
      [loadingCount]="5"
      loadingLabel="Carregando suas operações encerradas"
      errorTitle="Não conseguimos abrir suas operações encerradas"
      errorAction="carregar suas operações encerradas"
      emptyTitle="Você ainda não encerrou nenhuma operação"
      emptyReason="Esta tela mostra o que você já vendeu: lucro apurado, imposto do mês e prejuízo a compensar. Ela se preenche quando existe uma venda registrada."
      emptyNextStep="Registrar a venda em Posições apura o imposto pelo mês inteiro, e não pela ordem em que você lançou."
      emptyActionLabel="Ver minhas posições"
      emptyActionRoute="/patrimonio/posicoes"
      (retry)="recarregar()"
    >
      @if (closedTrades(); as ct) {
        @if (ct.trades.length > 0) {
          <div class="fi-block mt-6">
            <div class="flex items-center justify-between mb-3">
              <h2 class="fi-title m-0 text-ink">Total do período</h2>
              <button
                type="button"
                class="btn-quiet"
                (click)="showClosedTrades.set(!showClosedTrades())"
              >
                <lucide-icon
                  [name]="showClosedTrades() ? 'chevron-up' : 'chevron-down'"
                  size="16"
                ></lucide-icon>
                {{ showClosedTrades() ? 'Recolher' : 'Expandir' }}
              </button>
            </div>

            @if (ct.has_more) {
              <p class="fi-body text-ink-2 m-0 mb-3">
                Mostrando {{ ct.trades.length }} de {{ ct.total_count }} operações. Os totais acima
                cobrem todas — só a lista está cortada.
              </p>
            }

            @if (showClosedTrades()) {
              <dl class="flex flex-wrap gap-x-12 gap-y-5 m-0 mb-4 pt-4 border-t border-hairline">
                <div>
                  <dt class="fi-eyebrow text-ink-3">
                    {{ ct.total_realized_pnl >= 0 ? 'Lucro realizado' : 'Prejuízo realizado' }}
                  </dt>
                  <dd class="fi-metric text-ink m-0 mt-1">
                    {{ ct.total_realized_pnl >= 0 ? '+' : '−' }}R$
                    {{ absoluto(ct.total_realized_pnl) | number: '1.2-2' }}
                  </dd>
                </div>
                <div>
                  <dt class="fi-eyebrow text-ink-3">
                    IR apurado
                    <app-help-tooltip
                      term="IR apurado"
                      text="A lei apura ganho de capital por mês e por categoria: lucros e prejuízos do
                          mesmo mês se compensam, e o imposto incide sobre o líquido. É a soma da
                          coluna IR devido da tabela abaixo."
                    />
                  </dt>
                  <dd class="fi-metric text-ink m-0 mt-1">
                    R$ {{ ct.total_ir_paid | number: '1.2-2' }}
                  </dd>
                </div>
              </dl>

              @if (ct.total_tax_loss_available > 0) {
                <div class="p-4 rounded-md bg-brand/10 border border-brand/30 mb-4">
                  <div class="flex items-start gap-3">
                    <lucide-icon name="receipt" size="18" class="text-brand mt-0.5"></lucide-icon>
                    <div>
                      <div class="fi-label text-ink">
                        R$ {{ ct.total_tax_loss_available | number: '1.2-2' }} de prejuízo
                        disponível para compensar IR
                      </div>
                      <div class="fi-body text-ink-2 mt-1">
                        Já é considerado automaticamente ao estimar o IR das próximas vendas.
                      </div>
                      <ul class="fi-caption list-disc pl-4 text-ink-2 mt-2 m-0">
                        @for (balance of ct.tax_loss_balances; track balance.category) {
                          @if (balance.available > 0) {
                            <li>
                              {{ categoryLabel(balance.category) }}: R$
                              {{ balance.available | number: '1.2-2' }}
                              @if (balance.offset_used > 0) {
                                <span class="opacity-70">
                                  (R$ {{ balance.offset_used | number: '1.2-2' }} já usados)
                                </span>
                              }
                            </li>
                          }
                        }
                      </ul>
                    </div>
                  </div>
                </div>
              }

              @if (ct.months.length > 0) {
                <h3 class="fi-title text-ink m-0 mb-1">Apuração por mês</h3>
                <p class="fi-caption text-ink-2 m-0 mb-3">
                  O imposto é do mês, não da venda. Cada linha é um mês fechado numa categoria — é
                  este número que vai para o DARF.
                </p>

                <div class="overflow-x-auto mb-6">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th scope="col">Mês</th>
                        <th scope="col">Categoria</th>
                        <th scope="col" class="num">Vendido</th>
                        <th scope="col" class="num">Resultado</th>
                        <th scope="col" class="num">Compensado</th>
                        <th scope="col" class="num">IR devido</th>
                        <th scope="col">Por quê</th>
                      </tr>
                    </thead>
                    <tbody>
                      @for (m of ct.months; track m.month + m.category) {
                        <tr>
                          <td class="fi-label text-ink">{{ mesPorExtenso(m.month) }}</td>
                          <td class="text-ink-2">{{ categoryLabel(m.category) }}</td>
                          <td class="num text-ink">R$ {{ m.gross_sales | number: '1.2-2' }}</td>
                          <td
                            class="num"
                            [class.text-up]="m.result >= 0"
                            [class.text-down]="m.result < 0"
                          >
                            {{ m.result >= 0 ? '+' : '−' }}R$
                            {{ absoluto(m.result) | number: '1.2-2' }}
                          </td>
                          <td class="num text-ink-2">
                            {{
                              m.loss_offset_used > 0 ? (m.loss_offset_used | number: '1.2-2') : '—'
                            }}
                          </td>
                          <td class="num fi-label text-ink">
                            R$ {{ m.ir_amount | number: '1.2-2' }}
                          </td>
                          <td class="fi-caption text-ink-2">{{ m.observation }}</td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              }

              <h3 class="fi-title text-ink m-0 mb-3">Vendas</h3>

              <div style="overflow-x: auto">
                <table class="fi-body w-full border-collapse">
                  <thead>
                    <tr class="border-b border-hairline">
                      <th class="fi-label text-left py-2 px-2 text-ink-2">Ativo</th>
                      <th class="fi-label text-left py-2 px-2 text-ink-2">Data</th>
                      <th class="fi-label text-right py-2 px-2 text-ink-2">Qtd</th>
                      <th class="fi-label text-right py-2 px-2 text-ink-2">P. médio</th>
                      <th class="fi-label text-right py-2 px-2 text-ink-2">P. venda</th>
                      <th class="fi-label text-right py-2 px-2 text-ink-2">Compensado</th>
                      <th class="fi-label text-right py-2 px-2 text-ink-2">
                        IR (rateio)
                        <app-help-tooltip
                          term="IR rateado"
                          text="O imposto é apurado no mês inteiro; aqui ele aparece dividido entre as
                              vendas lucrativas daquele mês, em proporção ao lucro de cada uma."
                        />
                      </th>
                      <th class="fi-label text-right py-2 px-2 text-ink-2">Lucro líquido</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (t of ct.trades; track t.id) {
                      <tr class="border-b border-hairline hover:bg-ground-2 transition-colors">
                        <td class="fi-label py-2 px-2 text-ink">{{ t.ticker }}</td>
                        <td class="py-2 px-2 text-ink">
                          {{ t.sold_at * 1000 | date: 'dd/MM/yyyy' }}
                        </td>
                        <td class="text-right py-2 px-2 text-ink">{{ t.quantity }}</td>
                        <td class="text-right py-2 px-2 text-ink">
                          {{ t.avg_price | number: '1.2-2' }}
                        </td>
                        <td class="text-right py-2 px-2 text-ink">
                          {{ t.sell_price | number: '1.2-2' }}
                        </td>
                        <td class="text-right py-2 px-2 text-ink-2">
                          {{
                            t.loss_offset_used > 0 ? (t.loss_offset_used | number: '1.2-2') : '—'
                          }}
                        </td>
                        <td class="text-right py-2 px-2 text-ink">
                          {{ t.ir_amount | number: '1.2-2' }}
                        </td>
                        <td
                          class="fi-label text-right py-2 px-2"
                          [class.text-up]="t.net_profit >= 0"
                          [class.text-down]="t.net_profit < 0"
                        >
                          {{ t.net_profit >= 0 ? '+' : '' }}R$ {{ t.net_profit | number: '1.2-2' }}
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
            }
          </div>
        }
      }
    </app-async-state>
  `,
})
export class ClosedTradesComponent implements OnInit {
  private readonly store = inject(CarteiraStore);
  readonly ui = inject(UiHelperService);

  readonly closedTrades = this.store.closedTrades;
  readonly carregando = this.store.carregando;
  readonly erroDeCarga = this.store.erroDeCarga;
  readonly vazio = this.store.isEmpty;
  readonly showClosedTrades = signal(true);

  recarregar(): void {
    this.store.reload();
  }

  ngOnInit(): void {
    this.store.ensureLoaded();
  }

  absoluto(valor: number): number {
    return Math.abs(valor);
  }

  categoryLabel(category: string): string {
    return this.ui.categoryLabel(category);
  }

  mesPorExtenso(mes: string): string {
    const [ano, numero] = mes.split('-');
    const nomes = [
      'jan',
      'fev',
      'mar',
      'abr',
      'mai',
      'jun',
      'jul',
      'ago',
      'set',
      'out',
      'nov',
      'dez',
    ];
    const nome = nomes[Number(numero) - 1];
    return nome ? `${nome}/${ano}` : mes;
  }
}
