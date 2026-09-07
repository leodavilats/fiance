import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  CashKind,
  CashflowService,
  FiCategoria,
  mesCorrente,
  nomeDoMes,
  fiCategoriasDeDespesa,
  fiCategoriasDeEntrada,
} from '../../core';
import { PageHeaderComponent } from '../page-header/page-header.component';

@Component({
  selector: 'app-month-entry',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    LucideAngularModule,
    PageHeaderComponent,
  ],
  template: `
    <app-page-header
      title="Lançar no mês"
      question="O que entrou ou saiu?"
      scope="A leitura do mês fica em Mês; aqui é só a escrita."
    />

    <form class="fi-block" [formGroup]="form" (ngSubmit)="enviar()">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="field">
          <label class="field-label" for="lanc-kind">Tipo</label>
          <select id="lanc-kind" class="input" formControlName="kind" (change)="trocarTipo()">
            <option value="expense">Saída</option>
            <option value="income">Entrada</option>
          </select>
        </div>

        <div class="field">
          <label class="field-label" for="lanc-categoria">Categoria</label>
          <select id="lanc-categoria" class="input" formControlName="category">
            @for (c of categorias(); track c.id) {
              <option [value]="c.id">{{ c.label }}</option>
            }
          </select>
        </div>

        <div class="field sm:col-span-2">
          <label class="field-label" for="lanc-descricao">Descrição</label>
          <input
            id="lanc-descricao"
            class="input"
            type="text"
            formControlName="description"
            maxlength="120"
            placeholder="Aluguel, mercado da semana, salário…"
          />
        </div>

        <div class="field">
          <label class="field-label" for="lanc-valor">Valor (R$)</label>
          <input
            id="lanc-valor"
            class="input"
            type="number"
            formControlName="amount"
            min="0.01"
            step="0.01"
          />
          <p class="field-hint">
            Sempre positivo: entrada e saída se distinguem pelo tipo, não pelo sinal.
          </p>
        </div>

        <div class="field">
          <label class="field-label" for="lanc-vencimento">Vencimento</label>
          <input id="lanc-vencimento" class="input" type="date" formControlName="due_on" />
        </div>

        <div class="field sm:col-span-2">
          <label class="fi-body flex items-center gap-2 cursor-pointer text-ink">
            <input type="checkbox" formControlName="pago" class="cursor-pointer" />
            Já foi pago
          </label>
          <p class="field-hint">
            O caixa mede quando o dinheiro se moveu. Conta não paga entra como comprometida e
            aparece em "a vencer".
          </p>
        </div>

        @if (pagoMarcado()) {
          <div class="field">
            <label class="field-label" for="lanc-pagamento">Dia do pagamento</label>
            <input id="lanc-pagamento" class="input" type="date" formControlName="paid_on" />
          </div>
        }
      </div>

      @if (erro()) {
        <p class="fi-caption text-adverse m-0 mt-4" role="alert">{{ erro() }}</p>
      }
      @if (salvo(); as m) {
        <div class="notice notice-favorable mt-4">
          <lucide-icon name="check" size="18" aria-hidden="true"></lucide-icon>
          <p class="fi-body m-0">
            Lançado em <strong>{{ nome(m) }}</strong
            >.
            <a
              [routerLink]="['/mes']"
              [queryParams]="{ mes: m === atual ? null : m }"
              class="btn-link"
            >
              Ver {{ m === atual ? 'o mês' : nome(m) }}
            </a>
          </p>
        </div>
      }

      <div class="flex items-center gap-3 mt-5">
        <button type="submit" class="btn-primary" [disabled]="salvando() || form.invalid">
          <lucide-icon name="plus" size="16" aria-hidden="true"></lucide-icon>
          {{ salvando() ? 'Salvando…' : 'Lançar' }}
        </button>
        <a routerLink="/mes" class="btn-secondary no-underline">Voltar ao mês</a>
      </div>
    </form>
  `,
})
export class MonthEntryComponent {
  readonly nome = nomeDoMes;
  readonly atual = mesCorrente();

  private readonly api = inject(CashflowService);
  private readonly fb = inject(FormBuilder);

  readonly salvando = signal(false);
  /** O mês em que o último lançamento caiu, ou vazio. */
  readonly salvo = signal('');
  readonly erro = signal('');
  readonly pagoMarcado = signal(true);

  readonly form = this.fb.group({
    kind: this.fb.control<CashKind>('expense', { nonNullable: true }),
    category: this.fb.control('moradia', { nonNullable: true }),
    description: this.fb.control('', {
      nonNullable: true,
      validators: [Validators.required, Validators.maxLength(120)],
    }),
    amount: this.fb.control<number | null>(null, [Validators.required, Validators.min(0.01)]),
    due_on: this.fb.control(hojeIso(), { nonNullable: true, validators: [Validators.required] }),
    pago: this.fb.control(true, { nonNullable: true }),
    paid_on: this.fb.control(hojeIso(), { nonNullable: true }),
  });

  constructor() {
    this.form.controls.pago.valueChanges.subscribe(v => this.pagoMarcado.set(v));
  }

  categorias(): { id: string; label: string }[] {
    const mapa =
      this.form.controls.kind.value === 'income' ? fiCategoriasDeEntrada : fiCategoriasDeDespesa;

    return Object.entries(mapa)
      .filter(([id]) => id !== 'provento')
      .map(([id, c]) => ({ id, label: (c as FiCategoria).label }));
  }

  trocarTipo(): void {
    const primeira = this.categorias()[0];
    if (primeira) this.form.controls.category.setValue(primeira.id);
  }

  enviar(): void {
    if (this.form.invalid || this.salvando()) return;

    const v = this.form.getRawValue();
    const competencia = (v.pago ? v.paid_on : v.due_on).slice(0, 7);
    this.salvando.set(true);
    this.erro.set('');
    this.salvo.set('');

    this.api
      .addEntry({
        kind: v.kind,
        category: v.category,
        description: v.description,
        amount: Number(v.amount),
        due_on: v.due_on,
        paid_on: v.pago ? v.paid_on : null,
      })
      .subscribe({
        next: () => {
          this.salvando.set(false);
          this.salvo.set(competencia);
          this.form.patchValue({ description: '', amount: null });
        },
        error: resposta => {
          this.salvando.set(false);
          this.erro.set(
            resposta?.error?.detail ??
              'Não consegui lançar agora. Confira os campos e tente de novo.'
          );
        },
      });
  }
}

function hojeIso(): string {
  return new Date().toISOString().slice(0, 10);
}
