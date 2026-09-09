import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { QuickInvestResponse, RecommendService, UiHelperService } from '../../core';
import { PageHeaderComponent } from '../page-header/page-header.component';
import { ProvenanceComponent } from '../provenance/provenance.component';
import { SectionComponent } from '../section/section.component';
import { SkeletonComponent } from '../skeleton/skeleton.component';

@Component({
  selector: 'app-quick-invest',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    LucideAngularModule,
    PageHeaderComponent,
    ProvenanceComponent,
    SectionComponent,
    SkeletonComponent,
  ],
  template: `
    <app-page-header
      title="Onde aportar"
      question="Recebi dinheiro — onde ele faz mais diferença agora?"
    />

    @if (carregando()) {
      <app-skeleton shape="metric" />
    } @else if (erro()) {
      <div class="notice notice-adverse">
        <lucide-icon name="circle-alert" size="18" aria-hidden="true"></lucide-icon>
        <div>
          <p class="fi-label m-0">Não conseguimos montar a ordem agora</p>
          <p class="fi-body m-0 mt-1">
            Pode ser a fonte de cotações. Seus lançamentos e sua carteira continuam intactos.
          </p>
          <button type="button" class="btn-secondary mt-3" (click)="montar(null)">
            Tentar de novo
          </button>
        </div>
      </div>
    } @else if (resultado(); as r) {
      <section class="fi-block">
        <p class="fi-verdict text-ink m-0 max-w-reading">{{ r.summary }}</p>

        <p class="fi-eyebrow text-ink-3 m-0 mt-6">
          {{ r.cash_source === 'cascade' ? 'A sua sobra deste mês' : 'O valor que você informou' }}
        </p>
        <p class="fi-money-xl text-ink m-0 mt-1">{{ reais(r.total_cash) }}</p>

        @if (r.cash_source === 'cascade') {
          <p class="fi-body text-ink-2 m-0 mt-2 max-w-reading">
            É o que resta depois da dívida e da reserva, na ordem que a
            <a routerLink="/sobra" class="btn-link">Sobra</a> calcula. Nada aqui foi digitado.
          </p>
        }

        <app-provenance
          summary="Como esta ordem foi montada"
          [method]="metodo()"
          source="Sua carteira e sua renda fixa, com preços da BRAPI e a alocação-alvo que você declarou."
          limitation="É uma ordem de prioridade, não recomendação de compra. Preço muda entre montar a ordem e executá-la, e a quantidade é sempre cota inteira."
        />

        <div class="mt-5 pt-4 border-t border-hairline flex flex-wrap items-end gap-3">
          <div class="field max-w-[12rem]">
            <label class="field-label" for="outro-valor">Simular outro valor</label>
            <input
              id="outro-valor"
              type="number"
              class="input"
              min="1"
              [formControl]="valor"
              placeholder="R$"
            />
          </div>
          <button
            type="button"
            class="btn-secondary"
            [disabled]="valor.invalid || valor.value === null"
            [attr.title]="
              valor.value === null
                ? 'Informe um valor para recalcular'
                : valor.invalid
                  ? 'O valor precisa ser maior que zero'
                  : null
            "
            (click)="montar(valor.value)"
          >
            Recalcular
          </button>
          @if (r.cash_source === 'informed') {
            <button type="button" class="btn-link" (click)="usarASobra()">
              Voltar para a sobra
            </button>
          }
        </div>
      </section>

      @if (r.allocations.length > 0) {
        <app-section title="A ordem" [count]="r.allocations.length">
          <div class="overflow-x-auto mt-3">
            <table class="data-table">
              <caption class="sr-only">
                Ativos da ordem, com quanto e por que cada um entrou
              </caption>
              <thead>
                <tr>
                  <th scope="col">Ativo</th>
                  <th scope="col">Por que este</th>
                  <th scope="col" class="num">Cotas</th>
                  <th scope="col" class="num">Valor</th>
                </tr>
              </thead>
              <tbody>
                @for (a of r.allocations; track a.ticker) {
                  <tr>
                    <td>
                      <a [routerLink]="['/ativo', a.ticker]" class="fi-ticker text-brand">{{
                        a.ticker
                      }}</a>
                      <span class="fi-caption text-ink-3 block">{{
                        a.name || ui.categoryLabel(a.category)
                      }}</span>
                    </td>
                    <td class="text-ink-2">{{ a.rationale }}</td>
                    <td class="num">{{ a.suggested_quantity ?? '—' }}</td>
                    <td class="num">{{ reais(a.suggested_investment) }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </app-section>
      }

      @if (r.fixed_income; as rf) {
        <app-section title="Renda fixa">
          <p class="fi-body text-ink m-0">{{ reais(rf.amount) }}</p>
          <p class="fi-body text-ink-2 m-0 mt-1 max-w-reading">{{ rf.rationale }}</p>
          <a routerLink="/descobrir/renda-fixa" class="btn-link mt-2 inline-block">
            Comparar títulos
          </a>
        </app-section>
      }

      @if (semDestino().length > 0) {
        <app-section title="Sem destino" hint="Todo real que não entrou na ordem tem um motivo.">
          <ul class="list-none m-0 p-0 flex flex-col gap-2">
            @for (u of semDestino(); track u.reason) {
              <li class="fi-body text-ink-2 flex items-baseline gap-3">
                <span class="fi-num text-ink">{{ reais(u.value) }}</span>
                <span>{{ u.reason }}</span>
              </li>
            }
          </ul>
        </app-section>
      }

      @if (r.basis === 'score') {
        <app-section title="Sem alocação-alvo declarada">
          <p class="fi-body text-ink-2 m-0 max-w-reading">
            A ordem acima está por score, porque você ainda não disse quanto quer em cada categoria.
            Sem isso o produto não sabe onde este dinheiro deveria ir — e não vai inventar um alvo.
          </p>
          <a routerLink="/voce/objetivos" class="btn-primary no-underline mt-3">
            Declarar minha alocação-alvo
          </a>
        </app-section>
      }
    }
  `,
})
export class QuickInvestComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);

  readonly resultado = signal<QuickInvestResponse | null>(null);
  readonly carregando = signal(true);
  readonly erro = signal(false);

  readonly valor = this.fb.control<number | null>(null, [Validators.min(1)]);

  /** A resposta de uma API anterior a este contrato nao traz a lista. */
  readonly semDestino = computed(() => this.resultado()?.unallocated ?? []);

  readonly metodo = computed(() => {
    const r = this.resultado();
    if (r?.basis === 'goals') {
      return 'Compara sua alocação atual com a alocação-alvo e distribui o valor no que está mais abaixo do alvo. O score de cada ativo entra como desempate.';
    }
    return 'Ordena o universo por score e distribui o valor nos melhores que couberem, porque não há alocação-alvo declarada para comparar.';
  });

  ngOnInit(): void {
    this.montar(null);
  }

  usarASobra(): void {
    this.valor.reset();
    this.montar(null);
  }

  montar(valor: number | null): void {
    this.carregando.set(true);
    this.erro.set(false);

    this.svc.quickInvest({ cash_available: valor, min_order_value: 50 }).subscribe({
      next: r => {
        this.resultado.set(r);
        this.carregando.set(false);
      },
      error: () => {
        this.erro.set(true);
        this.carregando.set(false);
      },
    });
  }

  reais(valor: number | null | undefined): string {
    if (valor === null || valor === undefined) return '—';
    return valor.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
    });
  }
}
