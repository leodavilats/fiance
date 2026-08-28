import { CommonModule } from '@angular/common';
import { ProvenanceComponent } from '../provenance/provenance.component';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { QuickInvestResponse, RecommendService, UiHelperService } from '../../core';

@Component({
  selector: 'app-quick-invest',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule, ProvenanceComponent],
  templateUrl: './quick-invest.component.html',
})
export class QuickInvestComponent {
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);

  readonly quickInvestResult = signal<QuickInvestResponse | null>(null);
  readonly quickInvestLoading = signal(false);
  readonly quickInvestError = signal(false);

  readonly quickInvestForm = this.fb.nonNullable.group({
    cash_available: [1000, [Validators.required, Validators.min(1)]],
    min_order_value: [50, [Validators.required, Validators.min(1)]],
    use_current_goals: [true],
    prioritize_rebalance: [true],
  });

  runQuickInvest(): void {
    if (this.quickInvestForm.invalid) return;
    this.quickInvestLoading.set(true);
    this.quickInvestError.set(false);
    this.quickInvestResult.set(null);

    const v = this.quickInvestForm.getRawValue();
    this.svc
      .quickInvest({
        cash_available: v.cash_available,
        use_current_goals: v.use_current_goals,
        prioritize_rebalance: v.prioritize_rebalance,
        min_order_value: v.min_order_value,
      })
      .subscribe({
        next: r => {
          this.quickInvestResult.set(r);
          this.quickInvestLoading.set(false);
          this.svc.saveCashAvailable(v.cash_available).subscribe({ error: () => {} });
        },
        error: () => {
          this.quickInvestError.set(true);
          this.quickInvestLoading.set(false);
        },
      });
  }
}
