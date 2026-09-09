import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { PassiveIncomeProjectionResponse, RecommendService } from '../../../core';
import { AsyncStateComponent } from '../../async-state/async-state.component';
import { RangeComponent } from '../../range/range.component';
import { PageHeaderComponent } from '../../page-header/page-header.component';

@Component({
  selector: 'app-contribution-simulator',
  standalone: true,
  imports: [
    PageHeaderComponent,
    CommonModule,
    ReactiveFormsModule,
    AsyncStateComponent,
    RangeComponent,
  ],
  template: `
    <div class="flex flex-col gap-4">
      <app-page-header
        title="Projeção"
        question="Se eu aportar todo mês, como a carteira e a renda passiva evoluiriam?"
      />

      <form [formGroup]="form" (ngSubmit)="simulate()" class="fi-block">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="field-label block mb-1.5">Aporte mensal (R$)</label>
            <input type="number" formControlName="monthly_contribution" class="input" />
          </div>
          <div>
            <label class="field-label block mb-1.5">Período (meses)</label>
            <input type="number" formControlName="months_ahead" class="input" />
          </div>
          <div>
            <label class="field-label block mb-1.5">Valorização anual esperada (%)</label>
            <input type="number" formControlName="portfolio_growth_rate" class="input" />
          </div>
          <div>
            <label class="field-label block mb-1.5">Crescimento anual dos dividendos (%)</label>
            <input type="number" formControlName="dividend_growth_rate" class="input" />
          </div>
          <div>
            <label class="field-label block mb-1.5"
              >Meta de renda passiva mensal (R$, opcional)</label
            >
            <input type="number" formControlName="target_monthly_income" class="input" />
          </div>
          <div class="flex items-center gap-2 mt-6">
            <input
              type="checkbox"
              formControlName="reinvest_dividends"
              id="reinvest"
              class="w-4 h-4"
            />
            <label for="reinvest" class="fi-caption text-ink"
              >Reinvestir dividendos automaticamente</label
            >
          </div>
        </div>

        <div class="mt-6 pt-4 border-t border-hairline">
          <button type="submit" [disabled]="loading() || form.invalid" class="btn-primary">
            {{ loading() ? 'Simulando...' : 'Simular' }}
          </button>
        </div>
      </form>

      @if (erro()) {
        <app-async-state
          [error]="erro()"
          errorTitle="A projeção não foi calculada"
          errorAction="projetar sua carteira com esse aporte"
          (retry)="simulate()"
        />
      }

      @if (result(); as r) {
        <p class="fi-caption text-ink-2 m-0">{{ r.disclaimer }}</p>

        <dl class="flex flex-wrap gap-x-12 gap-y-5 m-0 pt-4 border-t border-hairline">
          <div>
            <dt class="fi-eyebrow text-ink-3">Hoje</dt>
            <dd class="fi-metric-sm text-ink m-0 mt-1">
              R$ {{ r.current_portfolio_value | number: '1.0-0' }}
            </dd>
            <dd class="fi-caption text-ink-3 m-0">
              R$ {{ r.current_passive_income_monthly | number: '1.2-2' }}/mês
            </dd>
          </div>
          <div
            appRange
            [label]="'Carteira em ' + form.getRawValue().months_ahead + ' meses'"
            [low]="ultimo(r).portfolio_value_low"
            [high]="ultimo(r).portfolio_value_high"
            [base]="ultimo(r).portfolio_value"
          ></div>
          <div
            appRange
            label="Renda passiva/mês no fim"
            [low]="ultimo(r).passive_income_monthly_low"
            [high]="ultimo(r).passive_income_monthly_high"
            [base]="ultimo(r).passive_income_monthly"
            [cents]="true"
          ></div>
        </dl>

        <div class="overflow-x-auto">
          <table class="data-table">
            <caption class="sr-only">
              Renda passiva ao fim do período em cada cenário, com o motivo de cada um
            </caption>
            <thead>
              <tr>
                <th scope="col">Cenário</th>
                <th scope="col" class="num">Renda/mês no fim</th>
                <th scope="col">Por quê</th>
              </tr>
            </thead>
            <tbody>
              @for (s of r.scenarios; track s.code) {
                <tr>
                  <th scope="row" class="fi-label text-ink">{{ s.label }}</th>
                  <td class="num">R$ {{ s.final_passive_income_monthly | number: '1.2-2' }}</td>
                  <td class="text-ink-2">{{ s.rationale }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>

        @if (r.target; as meta) {
          <div class="notice notice-brand fi-body text-ink">
            Meta de <strong>R$ {{ meta.monthly_income | number: '1.2-2' }}/mês</strong>:
            @if (meta.reached_in_all_scenarios) {
              alcançada entre <strong>{{ meta.earliest_months }}</strong> e
              <strong>{{ meta.latest_months }} meses</strong> ({{ meta.earliest_date }} a
              {{ meta.latest_date }}). No cenário base, {{ meta.expected_months }} meses.
            } @else if (meta.expected_months) {
              alcançada em <strong>{{ meta.expected_months }} meses</strong> no cenário base, mas
              <strong>não é alcançada no cenário conservador</strong> dentro do período simulado.
            } @else {
              não é alcançada em nenhum dos três cenários dentro do período simulado. Aumentar o
              aporte mensal ou o prazo muda isso; mudar a premissa de valorização não.
            }
          </div>
        }

        <div class="overflow-x-auto border-t border-hairline">
          <table class="fi-body w-full">
            <caption class="sr-only">
              Projeção mês a mês, com piso e teto entre os três cenários.
            </caption>
            <thead>
              <tr class="fi-caption bg-ground-2 text-ink-2">
                <th scope="col" class="fi-label text-left px-3 py-2">Mês</th>
                <th scope="col" class="fi-label text-right px-3 py-2">Carteira (faixa)</th>
                <th scope="col" class="fi-label text-right px-3 py-2">Renda/mês (faixa)</th>
              </tr>
            </thead>
            <tbody>
              @for (m of milestones(r); track m.month) {
                <tr class="border-t border-hairline">
                  <td class="px-3 py-2 text-ink">{{ m.month }}</td>
                  <td class="px-3 py-2 text-right text-ink">
                    R$ {{ m.portfolio_value_low | number: '1.0-0' }} – R$
                    {{ m.portfolio_value_high | number: '1.0-0' }}
                  </td>
                  <td class="px-3 py-2 text-right text-ink">
                    R$ {{ m.passive_income_monthly_low | number: '1.2-2' }} – R$
                    {{ m.passive_income_monthly_high | number: '1.2-2' }}
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>

        <div class="fi-caption text-ink-2">
          {{ r.assumptions['scenario_spread'] }}
        </div>
      }
    </div>
  `,
})
export class ContributionSimulatorComponent {
  private api = inject(RecommendService);
  private fb = inject(FormBuilder);

  loading = signal(false);
  result = signal<PassiveIncomeProjectionResponse | null>(null);
  readonly erro = signal<unknown>(null);

  form: FormGroup = this.fb.group({
    monthly_contribution: this.fb.control(500, {
      nonNullable: true,
      validators: [Validators.min(0)],
    }),
    months_ahead: this.fb.control(60, {
      nonNullable: true,
      validators: [Validators.min(1), Validators.max(240)],
    }),
    portfolio_growth_rate: this.fb.control(10, {
      nonNullable: true,
      validators: [Validators.min(0), Validators.max(50)],
    }),
    dividend_growth_rate: this.fb.control(5, {
      nonNullable: true,
      validators: [Validators.min(0), Validators.max(30)],
    }),
    reinvest_dividends: this.fb.control(true, { nonNullable: true }),
    target_monthly_income: this.fb.control<number | null>(null),
  });

  simulate(): void {
    if (this.form.invalid) return;
    const v = this.form.getRawValue();
    this.loading.set(true);
    this.erro.set(null);
    this.api
      .projectPassiveIncome({
        monthly_contribution: v.monthly_contribution,
        months_ahead: v.months_ahead,
        portfolio_growth_rate: v.portfolio_growth_rate / 100,
        dividend_growth_rate: v.dividend_growth_rate / 100,
        reinvest_dividends: v.reinvest_dividends,
        target_monthly_income: v.target_monthly_income || undefined,
      })
      .subscribe({
        next: res => {
          this.result.set(res);
          this.loading.set(false);
        },
        error: err => {
          this.erro.set(err);
          this.loading.set(false);
        },
      });
  }

  ultimo(res: PassiveIncomeProjectionResponse) {
    return res.projections[res.projections.length - 1];
  }

  milestones(res: PassiveIncomeProjectionResponse) {
    const step = Math.max(1, Math.round(res.projections.length / 8));
    return res.projections.filter((_, i) => i % step === 0 || i === res.projections.length - 1);
  }
}
