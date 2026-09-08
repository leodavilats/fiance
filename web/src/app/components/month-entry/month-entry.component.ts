import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  CashEntry,
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
      [title]="editando() ? 'Editar lançamento' : 'Lançar no mês'"
      [question]="editando() ? 'O que estava errado?' : 'O que entrou ou saiu?'"
      scope="A leitura do mês fica em Mês; aqui é só a escrita."
    />

    @if (carregando()) {
      <p class="fi-body text-ink-2">Buscando o lançamento…</p>
    } @else {
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
            <label class="field-label" for="lanc-vencimento">
              {{ ehEntrada() ? 'Dia' : 'Vencimento' }}
            </label>
            <input id="lanc-vencimento" class="input" type="date" formControlName="due_on" />
            @if (ehEntrada()) {
              <p class="field-hint">
                O dia em que o dinheiro entra. Entrada não tem vencimento a cumprir — é a data do
                crédito, e ela sozinha já decide de que mês o lançamento é.
              </p>
            }
          </div>

          <div class="field sm:col-span-2">
            <label class="fi-body flex items-center gap-2 cursor-pointer text-ink">
              <input type="checkbox" formControlName="pago" class="cursor-pointer" />
              {{ ehEntrada() ? 'Já caiu na conta' : 'Já foi pago' }}
            </label>
            <p class="field-hint">
              @if (ehEntrada()) {
                O caixa mede quando o dinheiro se moveu. O que ainda não caiu não conta como entrada
                — aparece no mês como a receber.
              } @else {
                O caixa mede quando o dinheiro se moveu. Conta não paga entra como comprometida e
                aparece em "a vencer".
              }
            </p>
          </div>

          @if (pagoMarcado() && !ehEntrada()) {
            <div class="field">
              <label class="field-label" for="lanc-pagamento">Dia do pagamento</label>
              <input id="lanc-pagamento" class="input" type="date" formControlName="paid_on" />
              <p class="field-hint">Só difere do vencimento quando a conta foi paga fora do dia.</p>
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
              {{ editando() ? 'Atualizado' : 'Lançado' }} em <strong>{{ nome(m) }}</strong
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
            <lucide-icon
              [name]="editando() ? 'check' : 'plus'"
              size="16"
              aria-hidden="true"
            ></lucide-icon>
            {{ salvando() ? 'Salvando…' : editando() ? 'Salvar' : 'Lançar' }}
          </button>
          <a routerLink="/mes" class="btn-secondary no-underline">
            {{ editando() ? 'Cancelar' : 'Voltar ao mês' }}
          </a>
        </div>
      </form>
    }
  `,
})
export class MonthEntryComponent implements OnInit {
  readonly nome = nomeDoMes;
  readonly atual = mesCorrente();

  private readonly api = inject(CashflowService);
  private readonly fb = inject(FormBuilder);
  private readonly rota = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly salvando = signal(false);
  readonly carregando = signal(false);
  /** O mês em que o lançamento caiu, ou vazio. */
  readonly salvo = signal('');
  readonly erro = signal('');
  readonly pagoMarcado = signal(true);
  readonly tipo = signal<CashKind>('expense');

  /** O id em edição, ou nulo quando se está lançando. Mora na URL. */
  readonly editando = signal<number | null>(null);

  readonly ehEntrada = computed(() => this.tipo() === 'income');

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
    this.form.controls.kind.valueChanges.subscribe(v => this.tipo.set(v));
  }

  ngOnInit(): void {
    this.rota.queryParamMap.subscribe(params => {
      const id = Number(params.get('editar'));
      if (!id) {
        this.editando.set(null);
        return;
      }
      this.editando.set(id);
      this.buscar(id);
    });
  }

  private buscar(id: number): void {
    this.carregando.set(true);
    this.api.entries().subscribe({
      next: todas => {
        const alvo = todas.find(e => e.id === id);
        this.carregando.set(false);
        if (!alvo) {
          this.erro.set('Esse lançamento não existe mais.');
          this.editando.set(null);
          return;
        }
        this.preencher(alvo);
      },
      error: () => {
        this.carregando.set(false);
        this.erro.set('Não consegui buscar esse lançamento.');
      },
    });
  }

  private preencher(entry: CashEntry): void {
    this.tipo.set(entry.kind);
    this.pagoMarcado.set(entry.paid_on !== null);
    this.form.patchValue({
      kind: entry.kind,
      category: entry.category,
      description: entry.description,
      amount: entry.amount,
      due_on: entry.due_on,
      pago: entry.paid_on !== null,
      paid_on: entry.paid_on ?? entry.due_on,
    });
  }

  categorias(): { id: string; label: string }[] {
    const mapa = this.ehEntrada() ? fiCategoriasDeEntrada : fiCategoriasDeDespesa;

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
    // Entrada não tem vencimento a cumprir: o dia informado é o do crédito.
    const pagamento = v.pago ? (this.ehEntrada() ? v.due_on : v.paid_on) : null;
    const competencia = (pagamento ?? v.due_on).slice(0, 7);

    const payload = {
      kind: v.kind,
      category: v.category,
      description: v.description,
      amount: Number(v.amount),
      due_on: v.due_on,
      paid_on: pagamento,
    };

    this.salvando.set(true);
    this.erro.set('');
    this.salvo.set('');

    const id = this.editando();
    const chamada = id ? this.api.updateEntry(id, payload) : this.api.addEntry(payload);

    chamada.subscribe({
      next: () => {
        this.salvando.set(false);
        this.salvo.set(competencia);
        if (id) {
          void this.router.navigate(['/mes'], {
            queryParams: { mes: competencia === this.atual ? null : competencia },
          });
          return;
        }
        this.form.patchValue({ description: '', amount: null });
      },
      error: resposta => {
        this.salvando.set(false);
        this.erro.set(
          resposta?.error?.detail ?? 'Não consegui lançar agora. Confira os campos e tente de novo.'
        );
      },
    });
  }
}

function hojeIso(): string {
  return new Date().toISOString().slice(0, 10);
}
