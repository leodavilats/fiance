import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { PassiveIncomeProjectionResponse, RecommendService } from '../../../core';

@Component({
  selector: 'app-contribution-simulator',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './contribution-simulator.component.html',
})
export class ContributionSimulatorComponent {
  private api = inject(RecommendService);
  private fb = inject(FormBuilder);

  loading = signal(false);
  result = signal<PassiveIncomeProjectionResponse | null>(null);

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
        error: () => this.loading.set(false),
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
