import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { AssetAnalysis, LoadingService, RecommendService, UiHelperService } from '../../core';

interface AnalyzeForm {
  symbol: FormControl<string>;
  desired_yield: FormControl<number>;
}

@Component({
  selector: 'app-analyze',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  template: `
    <form class="p-5 rounded-lg bg-panel border border-border" [formGroup]="form" (ngSubmit)="submit()">
      <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-3 text-tx"><lucide-icon name="search" size="18"></lucide-icon> Análise detalhada</h2>
      <p class="text-sm text-muted mb-4">Ação BR (PETR4), FII (HGLG11), EUA (AAPL) ou cripto (BTC, ETH).</p>
      <div class="grid grid-cols-1 sm:grid-cols-[2fr_1fr] gap-4">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Ticker</label>
          <input type="text" class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent" formControlName="symbol" placeholder="ex.: VALE3" />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Yield desejado (Bazin)</label>
          <input type="number" class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent" formControlName="desired_yield" min="0.02" max="0.20" step="0.005" />
        </div>
      </div>
      <div class="flex items-center gap-3 mt-4">
        <button class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-accent text-white border-0 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity" type="submit" [disabled]="form.invalid || loading.loading()">
          <lucide-icon [name]="loading.loading() ? 'loader-circle' : 'search'" size="16"></lucide-icon>
          {{ loading.loading() ? 'Analisando...' : 'Analisar' }}
        </button>
      </div>
    </form>

    @if (result(); as a) {
      <div class="p-5 rounded-lg bg-panel border border-border">
        <div style="display:flex; gap:14px; align-items:baseline; flex-wrap:wrap;">
          <h2 class="text-xl font-bold m-0 text-tx">{{ a.symbol }} — {{ a.name }}</h2>
          <span class="tag">{{ ui.assetTypeLabel(a.asset_type) }}</span>
          <span class="tag" *ngIf="a.sector">{{ ui.translateSector(a.sector) }}</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
          <div class="p-4 rounded-lg bg-bg-2 border border-border info">
            <div class="text-xs text-muted mb-1">Preço atual</div>
            <div class="text-xl font-bold text-tx">{{ a.price | number: '1.2-2' }} {{ a.currency }}</div>
          </div>
          <div class="p-4 rounded-lg bg-bg-2 border border-border good">
            <div class="text-xs text-muted mb-1">Preço justo</div>
            <div class="text-xl font-bold text-tx">{{ a.fair_price.consensus != null ? (a.fair_price.consensus | number: '1.2-2') : '—' }}</div>
          </div>
          <div class="p-4 rounded-lg bg-bg-2 border border-border" [class.good]="(a.fair_price.margin_of_safety ?? 0) >= 0" [class.warn]="(a.fair_price.margin_of_safety ?? 0) < 0">
            <div class="text-xs text-muted mb-1">Margem de segurança</div>
            <div class="text-xl font-bold text-tx">
              {{ a.fair_price.margin_of_safety != null ? ((a.fair_price.margin_of_safety * 100) | number: '1.1-1') + '%' : '—' }}
            </div>
          </div>
          <div class="p-4 rounded-lg bg-bg-2 border border-border info">
            <div class="text-xs text-muted mb-1">Decisão</div>
            <div class="text-xl font-bold text-tx"><span class="verdict-pill" [class]="ui.verdictClass(a.decision.verdict)">{{ a.decision.label }}</span></div>
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5">
          <div>
            <h3 class="text-base font-semibold mb-3 text-tx">Preço justo</h3>
            <ul class="flex flex-col gap-2 list-none p-0 m-0">
              <li class="flex justify-between items-center py-1.5 border-b border-border"><span class="text-muted">Bazin</span><strong class="text-tx">{{ ui.fmtNum(a.fair_price.bazin) }}</strong></li>
              <li class="flex justify-between items-center py-1.5 border-b border-border"><span class="text-muted">Graham</span><strong class="text-tx">{{ ui.fmtNum(a.fair_price.graham) }}</strong></li>
              <li class="flex justify-between items-center py-1.5 border-b border-border"><span class="text-muted">Dividendo médio 5a</span><strong class="text-tx">{{ ui.fmtNum(a.fair_price.avg_dividend_5y) }}</strong></li>
            </ul>
          </div>
          <div>
            <h3 class="text-base font-semibold mb-3 text-tx">Indicadores técnicos</h3>
            <ul class="flex flex-col gap-2 list-none p-0 m-0">
              <li class="flex justify-between items-center py-1.5 border-b border-border"><span class="text-muted">Tendência</span><strong class="text-tx">{{ ui.trendLabel(a.technical.trend) }}</strong></li>
              <li class="flex justify-between items-center py-1.5 border-b border-border"><span class="text-muted">SMA 50 / 200</span><strong class="text-tx">{{ ui.fmtNum(a.technical.sma_50) }} / {{ ui.fmtNum(a.technical.sma_200) }}</strong></li>
              <li class="flex justify-between items-center py-1.5 border-b border-border"><span class="text-muted">RSI(14)</span><strong class="text-tx">{{ ui.fmtNum(a.technical.rsi_14) }} {{ ui.rsiLabel(a.technical.rsi_14) }}</strong></li>
            </ul>
          </div>
          <div class="sm:col-span-2">
            <h3 class="text-base font-semibold mb-3 text-tx">Por que essa decisão?</h3>
            <ul class="list-disc pl-5 m-0 space-y-1">@for (r of a.decision.reasons; track r) {<li class="text-sm text-tx">{{ r }}</li>}</ul>
          </div>
        </div>
      </div>
    }
  `,
})
export class AnalyzeComponent implements OnInit {
  private fb = inject(FormBuilder);
  private svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  result = signal<AssetAnalysis | null>(null);

  form: FormGroup<AnalyzeForm> = this.fb.group({
    symbol: this.fb.control('VALE3', { nonNullable: true, validators: Validators.required }),
    desired_yield: this.fb.control(0.06, { nonNullable: true, validators: [Validators.min(0.02), Validators.max(0.20)] }),
  });

  ngOnInit(): void {}

  submit(): void {
    if (this.form.invalid) return;
    const { symbol, desired_yield } = this.form.getRawValue();
    this.svc.analyzeAsset(symbol, desired_yield).subscribe({
      next: (res) => {
        this.result.set(res);
      },
      error: () => {},
      complete: () => {},
    });
  }
}
