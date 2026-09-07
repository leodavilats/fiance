import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { CashflowService, Debt, fiTiposDeDivida } from '../../core';
import { HelpTooltipComponent } from '../help-tooltip/help-tooltip.component';
import { PageHeaderComponent } from '../page-header/page-header.component';

@Component({
  selector: 'app-month-debts',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    LucideAngularModule,
    PageHeaderComponent,
    HelpTooltipComponent,
  ],
  template: `
    <app-page-header
      title="Dívidas"
      question="Minha dívida é cara?"
      scope="A comparação é sempre contra o que a sua carteira rende — nunca um número de mercado."
    />

    <section class="fi-block">
      <h2 class="fi-title text-ink m-0">
        O que você deve
        <app-help-tooltip
          term="cara ou administrável"
          text="A classe sai da taxa, nunca do tipo de dívida: consignado a 0,4% ao mês e
                consignado a 3,5% não são a mesma decisão. Cara é a que custa mais que a sua
                carteira rende. Sem a taxa informada não há classe — o produto não estima taxa
                de rotativo, porque ela varia por banco e por dia."
        />
      </h2>

      @if (dividas().length === 0) {
        <p class="fi-body text-ink-2 m-0 mt-3 max-w-reading">
          Nenhuma dívida cadastrada. Se você tem alguma, informe o saldo e a taxa: é com os dois que
          a régua compara contra o que sua carteira rende, e decide se quitar vem antes de aportar.
        </p>
      } @else {
        <div class="overflow-x-auto mt-4">
          <table class="data-table">
            <caption class="sr-only">
              Dívidas cadastradas, com a taxa e a leitura de custo
            </caption>
            <thead>
              <tr>
                <th scope="col">Dívida</th>
                <th scope="col">Tipo</th>
                <th scope="col" class="num">Saldo</th>
                <th scope="col" class="num">Taxa/mês</th>
                <th scope="col">Leitura</th>
                <th scope="col"><span class="sr-only">Ação</span></th>
              </tr>
            </thead>
            <tbody>
              @for (d of dividas(); track d.id) {
                <tr>
                  <th scope="row" class="fi-label text-ink">{{ d.description }}</th>
                  <td class="text-ink-2">{{ rotuloDoTipo(d.kind) }}</td>
                  <td class="num">{{ reais(d.balance) }}</td>
                  <td class="num">
                    {{ d.monthly_rate === null ? '—' : d.monthly_rate + '%' }}
                  </td>
                  <td>
                    <span class="fi-label" [class]="classeDaLeitura(d)">
                      <lucide-icon [name]="iconeDaLeitura(d)" size="14" aria-hidden="true" />
                      {{ rotuloDaLeitura(d) }}
                    </span>
                    <span class="fi-caption text-ink-3 block mt-1">{{ explicacao(d) }}</span>
                  </td>
                  <td>
                    <button
                      type="button"
                      class="btn-secondary compact-btn"
                      (click)="quitar(d.id)"
                      [disabled]="quitando() === d.id"
                    >
                      {{ quitando() === d.id ? 'Quitando…' : 'Marcar como quitada' }}
                    </button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </section>

    <form class="fi-block" [formGroup]="form" (ngSubmit)="enviar()">
      <h2 class="fi-title text-ink m-0">Cadastrar dívida</h2>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        <div class="field">
          <label class="field-label" for="div-tipo">Tipo</label>
          <select id="div-tipo" class="input" formControlName="kind">
            @for (t of tipos; track t.id) {
              <option [value]="t.id">{{ t.label }}</option>
            }
          </select>
        </div>

        <div class="field">
          <label class="field-label" for="div-descricao">Descrição</label>
          <input
            id="div-descricao"
            class="input"
            type="text"
            formControlName="description"
            maxlength="120"
          />
        </div>

        <div class="field">
          <label class="field-label" for="div-saldo">Saldo devedor (R$)</label>
          <input
            id="div-saldo"
            class="input"
            type="number"
            formControlName="balance"
            min="0.01"
            step="0.01"
          />
        </div>

        <div class="field">
          <label class="field-label" for="div-taxa">Taxa ao mês (%)</label>
          <input
            id="div-taxa"
            class="input"
            type="number"
            formControlName="monthly_rate"
            min="0"
            step="0.01"
            placeholder="14,9"
          />
          <p class="field-hint">
            Sem a taxa a régua não aparece. O produto não a estima: rotativo varia por banco e por
            dia, e errar aqui é pior que não mostrar nada.
          </p>
        </div>
      </div>

      @if (erro()) {
        <p class="fi-caption text-adverse m-0 mt-4" role="alert">{{ erro() }}</p>
      }

      <button type="submit" class="btn-primary mt-5" [disabled]="salvando() || form.invalid">
        <lucide-icon name="plus" size="16" aria-hidden="true"></lucide-icon>
        {{ salvando() ? 'Salvando…' : 'Cadastrar' }}
      </button>
    </form>
  `,
})
export class MonthDebtsComponent implements OnInit {
  private readonly api = inject(CashflowService);
  private readonly fb = inject(FormBuilder);

  readonly dividas = signal<Debt[]>([]);
  readonly salvando = signal(false);
  readonly quitando = signal<number | null>(null);
  readonly erro = signal('');

  readonly tipos = Object.entries(fiTiposDeDivida).map(([id, label]) => ({ id, label }));

  readonly form = this.fb.group({
    kind: this.fb.control('rotativo_cartao', { nonNullable: true }),
    description: this.fb.control('', {
      nonNullable: true,
      validators: [Validators.required, Validators.maxLength(120)],
    }),
    balance: this.fb.control<number | null>(null, [Validators.required, Validators.min(0.01)]),
    monthly_rate: this.fb.control<number | null>(null, [Validators.min(0)]),
  });

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.api.debts().subscribe({ next: d => this.dividas.set(d) });
  }

  rotuloDoTipo(kind: string): string {
    return fiTiposDeDivida[kind] ?? kind;
  }

  rotuloDaLeitura(d: Debt): string {
    if (d.class === 'expensive') return 'Cara';
    if (d.class === 'manageable') return 'Administrável';
    return 'Sem taxa';
  }

  classeDaLeitura(d: Debt): string {
    if (d.class === 'expensive') return 'text-adverse';
    if (d.class === 'manageable') return 'text-favorable';
    return 'text-indeterminate';
  }

  iconeDaLeitura(d: Debt): string {
    if (d.class === 'expensive') return 'circle-alert';
    if (d.class === 'manageable') return 'check';
    return 'circle-help';
  }

  explicacao(d: Debt): string {
    if (d.class === 'no_rate') {
      return d.monthly_rate === null
        ? 'Sem a taxa não dá para comparar.'
        : 'Sem referência de rendimento para comparar.';
    }

    const referencia = d.reference_source === 'carteira' ? 'sua carteira' : 'o CDI';
    const alvo = d.reference_monthly?.toFixed(2) ?? '—';

    return d.class === 'expensive'
      ? `Custa mais que ${referencia}, que rende ${alvo}% ao mês. Quitar vem antes de aportar.`
      : `Custa menos que ${referencia}, que rende ${alvo}% ao mês. Quitar antecipado é decisão sua, não régua.`;
  }

  quitar(debtId: number | null): void {
    if (debtId === null) return;

    this.quitando.set(debtId);
    this.api.settleDebt(debtId).subscribe({
      next: () => {
        this.quitando.set(null);
        this.carregar();
      },
      error: () => this.quitando.set(null),
    });
  }

  enviar(): void {
    if (this.form.invalid || this.salvando()) return;

    const v = this.form.getRawValue();
    this.salvando.set(true);
    this.erro.set('');

    this.api
      .addDebt({
        kind: v.kind,
        description: v.description,
        balance: Number(v.balance),
        monthly_rate: v.monthly_rate === null ? null : Number(v.monthly_rate),
      })
      .subscribe({
        next: () => {
          this.salvando.set(false);
          this.form.patchValue({ description: '', balance: null, monthly_rate: null });
          this.carregar();
        },
        error: resposta => {
          this.salvando.set(false);
          this.erro.set(resposta?.error?.detail ?? 'Não consegui cadastrar agora.');
        },
      });
  }

  reais(valor: number): string {
    return valor.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
    });
  }
}
