import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormControl,
  FormArray,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import {
  AssetAnalysis,
  InvestmentStrategy,
  LoadingService,
  QuickInvestResponse,
  RecommendService,
  RendaFixaAsset,
  RendaFixaCompareResponse,
  ReferenceRates,
  UiHelperService,
} from '../../core';

type StrategyTab = 'analisar' | 'ajuste' | 'renda_fixa' | 'sugestao';

interface AnalyzeForm {
  symbol: FormControl<string>;
}

interface RendaFixaForm {
  tipo: FormControl<string>;
  nome: FormControl<string>;
  valor_investido: FormControl<number>;
  taxa: FormControl<number>;
  prazo_meses: FormControl<number>;
  tipo_taxa: FormControl<string>;
  percentual_cdi: FormControl<number | null>;
  liquidez: FormControl<string>;
}

@Component({
  selector: 'app-strategy',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  templateUrl: './strategy.component.html',
})
export class StrategyComponent implements OnInit {
  private fb = inject(FormBuilder);
  private svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  activeTab = signal<StrategyTab>('ajuste');
  strategy = signal<InvestmentStrategy | null>(null);
  analyzeResult = signal<AssetAnalysis | null>(null);
  rfResult = signal<RendaFixaCompareResponse | null>(null);
  referenceRates = signal<ReferenceRates | null>(null);
  quickInvestResult = signal<QuickInvestResponse | null>(null);
  quickInvestLoading = signal(false);
  quickInvestError = signal(false);

  analyzeForm: FormGroup<AnalyzeForm> = this.fb.group({
    symbol: this.fb.control('VALE3', { nonNullable: true, validators: Validators.required }),
  });

  quickInvestForm = this.fb.nonNullable.group({
    cash_available: [1000, [Validators.required, Validators.min(1)]],
    min_order_value: [50, [Validators.required, Validators.min(1)]],
    use_current_goals: [true],
    prioritize_rebalance: [true],
  });

  rfForms!: FormArray<FormGroup<RendaFixaForm>>;

  ngOnInit(): void {
    this.rfForms = this.fb.array<FormGroup<RendaFixaForm>>([this._makeRFGroup()]);
    this.loadStrategy();
    this.svc
      .getReferencRates()
      .subscribe({ next: r => this.referenceRates.set(r), error: () => {} });
  }

  private _makeRFGroup(): FormGroup<RendaFixaForm> {
    return this.fb.group<RendaFixaForm>({
      tipo: this.fb.control('cdb', { nonNullable: true }),
      nome: this.fb.control('', { nonNullable: true }),
      valor_investido: this.fb.control(10000, { nonNullable: true, validators: Validators.min(1) }),
      taxa: this.fb.control(12.0, { nonNullable: true, validators: Validators.min(0.01) }),
      prazo_meses: this.fb.control(12, { nonNullable: true, validators: Validators.min(1) }),
      tipo_taxa: this.fb.control('pre_fixado', { nonNullable: true }),
      percentual_cdi: this.fb.control<number | null>(110),
      liquidez: this.fb.control('no_vencimento', { nonNullable: true }),
    });
  }

  addRFAtivo(): void {
    this.rfForms.push(this._makeRFGroup());
  }
  removeRFAtivo(i: number): void {
    this.rfForms.removeAt(i);
  }

  onTipoChange(i: number): void {
    const ctrl = this.rfForms.controls[i];
    const tipo = ctrl.controls.tipo.value;

    if (['lci', 'lca', 'cri', 'cra'].includes(tipo)) {
      ctrl.controls.tipo_taxa.setValue('pos_fixado');
    } else if (tipo === 'tesouro_selic') {
      ctrl.controls.tipo_taxa.setValue('pos_fixado');
    } else if (tipo === 'tesouro_ipca') {
      ctrl.controls.tipo_taxa.setValue('hibrido');
    } else if (tipo === 'tesouro_pre') {
      ctrl.controls.tipo_taxa.setValue('pre_fixado');
    }
  }

  onTaxaTipoChange(i: number): void {
    const ctrl = this.rfForms.controls[i];
    if (ctrl.controls.tipo_taxa.value !== 'pos_fixado') {
      ctrl.controls.percentual_cdi.setValue(null);
    } else {
      ctrl.controls.percentual_cdi.setValue(110);
    }
  }

  compareRF(): void {
    const ativos: RendaFixaAsset[] = this.rfForms.controls.map(ctrl => {
      const v = ctrl.getRawValue();
      return {
        tipo: v.tipo as any,
        nome: v.nome || null,
        valor_investido: v.valor_investido,
        taxa: v.taxa,
        prazo_meses: v.prazo_meses,
        tipo_taxa: v.tipo_taxa as any,
        percentual_cdi: v.tipo_taxa === 'pos_fixado' ? v.percentual_cdi : null,
        liquidez: v.liquidez as any,
      };
    });

    const cdi = this.referenceRates()?.cdi_anual ?? null;
    const selic = this.referenceRates()?.selic_anual ?? null;

    this.svc.compareRendaFixa({ ativos, cdi_anual: cdi, selic_anual: selic }).subscribe({
      next: r => this.rfResult.set(r),
      error: () => {},
    });
  }

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
          this.loadStrategy();
        },
        error: () => {
          this.quickInvestError.set(true);
          this.quickInvestLoading.set(false);
        },
      });
  }

  loadStrategy(): void {
    const cash = this.quickInvestForm.getRawValue().cash_available;
    this.svc.getStrategy(cash).subscribe({
      next: data => this.strategy.set(data),
      error: () => {},
    });
  }

  submitAnalyze(): void {
    if (this.analyzeForm.invalid) return;
    const { symbol } = this.analyzeForm.getRawValue();
    this.svc.analyzeAsset(symbol).subscribe({
      next: res => this.analyzeResult.set(res),
      error: () => {},
    });
  }

  riskClass(risk: string): string {
    return { Baixo: 'tag-success', Médio: 'tag-warning', Alto: 'tag-danger' }[risk] || 'tag-muted';
  }

  totalToInvest(s: InvestmentStrategy): number {
    return s.suggestions.reduce((sum, x) => sum + x.invest_amount, 0);
  }

  verdictClassFromString(v: string): string {
    if (v === 'STRONG_BUY' || v === 'BUY') return 'v-buy';
    if (v === 'STRONG_SELL' || v === 'SELL') return 'v-sell';
    if (v === 'HOLD') return 'v-hold';
    return 'v-unknown';
  }

  assetLabel(type: string): string {
    return (
      { br_stock: 'Ação BR', fii: 'FII', us_stock: 'Ação EUA', crypto: 'Cripto' }[type] || type
    );
  }

  rfTipoLabel(tipo: string): string {
    return (
      {
        cdb: 'CDB',
        lci: 'LCI',
        lca: 'LCA',
        tesouro_selic: 'Tesouro Selic',
        tesouro_ipca: 'Tesouro IPCA+',
        tesouro_pre: 'Tesouro Pré',
        lc: 'LC',
        cri: 'CRI',
        cra: 'CRA',
      }[tipo] || tipo.toUpperCase()
    );
  }

  getCategoryBarColor(category: string): string {
    const colorMap: Record<string, string> = {
      renda_fixa: 'rgba(59, 130, 246, 0.6)',
      acoes_br: 'rgba(34, 197, 94, 0.6)',
      acoes_int: 'rgba(168, 85, 247, 0.6)',
      fiis: 'rgba(251, 191, 36, 0.6)',
      cripto: 'rgba(249, 115, 22, 0.6)',
    };
    return colorMap[category] || 'rgba(var(--accent) / 0.5)';
  }
}
