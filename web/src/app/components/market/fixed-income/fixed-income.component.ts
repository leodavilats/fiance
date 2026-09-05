import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import {
  FormArray,
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import {
  LoadingService,
  RecommendService,
  RendaFixaAsset,
  RendaFixaCompareResponse,
  ReferenceRates,
  UiHelperService,
} from '../../../core';
import { FixedIncomeRateComponent } from '../../fixed-income-rate/fixed-income-rate.component';

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
  selector: 'app-fixed-income',
  standalone: true,
  imports: [CommonModule, FixedIncomeRateComponent, LucideAngularModule, ReactiveFormsModule],
  template: `
    @if (referenceRates(); as taxas) {
      <p class="fi-caption text-ink-3 m-0 mb-6">
        Taxas de referência hoje — CDI
        <span class="fi-num text-ink-2">{{ taxas.cdi_anual | number: '1.2-2' }}%</span>, Selic
        <span class="fi-num text-ink-2">{{ taxas.selic_anual | number: '1.2-2' }}%</span>, IPCA
        <span class="fi-num text-ink-2">{{ taxas.ipca_anual | number: '1.2-2' }}%</span> ao ano.
      </p>
    }

    <div class="fi-block">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-3">
        <h2 class="fi-title m-0 text-ink">Simulador de renda fixa</h2>
        <button type="button" class="btn-secondary compact-btn" (click)="addRFAtivo()">
          <lucide-icon name="plus" size="15"></lucide-icon> Adicionar opção
        </button>
      </div>
      <p class="fi-body text-ink-2 mb-4">
        Insira uma ou mais opções para comparar. Identifica a melhor taxa líquida.
      </p>

      <div class="flex flex-col gap-4">
        @for (ctrl of rfForms.controls; track $index; let i = $index) {
          <div class="card" [formGroup]="ctrl">
            <div class="flex items-center justify-between mb-3">
              <div class="fi-label text-ink">Opção {{ i + 1 }}</div>
              @if (rfForms.length > 1) {
                <button
                  type="button"
                  class="btn-icon btn-icon-quiet btn-icon-danger"
                  (click)="removeRFAtivo(i)"
                  aria-label="Remover esta simulação"
                >
                  <lucide-icon name="x" size="14"></lucide-icon>
                </button>
              }
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 gap-y-5">
              <div>
                <label class="field-label block mb-1.5">Nome / Banco (opcional)</label>
                <input type="text" class="input" formControlName="nome" placeholder="ex.: Nubank" />
              </div>
              <div>
                <label class="field-label block mb-1.5">Tipo</label>
                <select
                  class="input cursor-pointer"
                  formControlName="tipo"
                  (change)="onTipoChange(i)"
                >
                  @for (t of ui.fixedIncomeTypes; track t.value) {
                    <option [value]="t.value">{{ t.label }}</option>
                  }
                </select>
              </div>
              <div>
                <label class="field-label block mb-1.5">Tipo de taxa</label>
                <select
                  class="input cursor-pointer"
                  formControlName="tipo_taxa"
                  (change)="onTaxaTipoChange(i)"
                >
                  <option value="pre_fixado">Pré-fixado</option>
                  <option value="pos_fixado">Pós-fixado (CDI)</option>
                  <option value="hibrido">Híbrido (IPCA+)</option>
                </select>
              </div>
              <div>
                <label class="field-label block mb-1.5">Valor investido (R$)</label>
                <input
                  type="number"
                  class="input"
                  formControlName="valor_investido"
                  min="100"
                  step="100"
                />
              </div>
              <div>
                <label class="field-label block mb-1.5">
                  @if (ctrl.controls['tipo_taxa'].value === 'pos_fixado') {
                    % do CDI
                  } @else {
                    Taxa a.a. (%)
                  }
                </label>
                <input
                  type="number"
                  class="input"
                  [formControlName]="
                    ctrl.controls['tipo_taxa'].value === 'pos_fixado' ? 'percentual_cdi' : 'taxa'
                  "
                  min="0.1"
                  step="0.1"
                  [placeholder]="
                    ctrl.controls['tipo_taxa'].value === 'pos_fixado' ? 'ex.: 110' : 'ex.: 12.5'
                  "
                />
              </div>
              <div>
                <label class="field-label block mb-1.5">Prazo (meses)</label>
                <input type="number" class="input" formControlName="prazo_meses" min="1" step="1" />
              </div>
              <div>
                <label class="field-label block mb-1.5">Liquidez</label>
                <select class="input cursor-pointer" formControlName="liquidez">
                  @for (l of ui.liquidityOptions; track l.value) {
                    <option [value]="l.value">{{ l.label }}</option>
                  }
                </select>
              </div>
            </div>
          </div>
        }
      </div>

      <div class="flex items-center gap-3 mt-4">
        <button
          type="button"
          class="btn-primary"
          (click)="compareRF()"
          [disabled]="loading.loading()"
        >
          <lucide-icon
            [name]="loading.loading() ? 'loader-circle' : 'calculator'"
            size="16"
          ></lucide-icon>
          {{
            loading.loading()
              ? 'Calculando...'
              : rfForms.length > 1
                ? 'Comparar opções'
                : 'Calcular rendimento'
          }}
        </button>
      </div>
    </div>

    @if (rfResult(); as result) {
      <div class="fi-block">
        <h2 class="fi-title m-0 mb-1 text-ink">Resultado da análise</h2>
        <p class="fi-caption text-ink-3 m-0 mb-5">
          Calculado sobre CDI
          <span class="fi-num">{{ result.cdi_referencia | number: '1.2-2' }}%</span>, Selic
          <span class="fi-num">{{ result.selic_referencia | number: '1.2-2' }}%</span> e IPCA
          <span class="fi-num">{{ result.ipca_referencia | number: '1.2-2' }}%</span> ao ano —
          {{
            result.fonte_taxas === 'bcb'
              ? 'séries do Banco Central'
              : 'estimativa, sem série do BCB'
          }}. Rendimento passado de um indexador não é promessa sobre o futuro dele.
        </p>

        @if (result.melhor_opcao_motivo) {
          <p class="notice notice-brand fi-body text-ink m-0 mb-5">
            {{ result.melhor_opcao_motivo }}
          </p>
        }

        <div class="flex flex-col gap-6">
          @for (r of result.resultados; track $index; let idx = $index) {
            <div
              class="pt-5 border-t"
              [class.border-brand]="r.melhor_opcao"
              [class.border-hairline]="!r.melhor_opcao"
            >
              <div class="flex items-start justify-between gap-4 flex-wrap mb-3">
                <div class="min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="fi-metric-sm text-ink">{{ r.nome || rfTipoLabel(r.tipo) }}</span>
                    <span class="tag tag-neutral">{{ rfTipoLabel(r.tipo) }}</span>
                    @if (r.isento_ir) {
                      <span class="tag tag-neutral">Isento de IR</span>
                    }
                    @if (r.liquidez === 'diaria') {
                      <span class="tag tag-neutral">Liquidez D+1</span>
                    }
                    @if (r.melhor_opcao) {
                      <span class="tag tag-brand">Melhor taxa líquida</span>
                    }
                  </div>
                  @if (r.isento_ir && r.pct_cdi_bruto_equivalente) {
                    <p class="fi-caption text-ink-3 m-0 mt-1.5">
                      Sem IR, equivale a um CDB de
                      <span class="fi-num">{{ r.pct_cdi_bruto_equivalente | number: '1.1-1' }}</span
                      >% do CDI.
                    </p>
                  }
                </div>
                <div class="text-right shrink-0">
                  <app-fixed-income-rate
                    label="Rende"
                    [netRatePct]="r.taxa_liquida_aa"
                    [pctOfCdi]="r.taxa_equivalente_cdi_pct"
                    [rateKind]="rateKindAt(idx)"
                    [contractedRate]="contractedRateAt(idx)"
                    [prazoMeses]="r.prazo_meses"
                    [liquidez]="r.liquidez"
                    [isentoIr]="r.isento_ir"
                    [irAliquotaPct]="r.ir.aliquota_pct"
                  />
                </div>
              </div>

              <table class="data-table">
                <caption class="sr-only">
                  Como
                  {{
                    r.nome || rfTipoLabel(r.tipo)
                  }}
                  chega ao valor líquido em
                  {{
                    r.prazo_meses
                  }}
                  meses
                </caption>
                <tbody>
                  <tr>
                    <td class="text-ink-2">Investido</td>
                    <td class="num">R$ {{ r.valor_investido | number: '1.2-2' }}</td>
                  </tr>
                  <tr>
                    <td class="text-ink-2">Rendimento bruto</td>
                    <td class="num text-up">+R$ {{ r.rendimento_bruto | number: '1.2-2' }}</td>
                  </tr>
                  @if (!r.isento_ir) {
                    <tr>
                      <td class="text-ink-2">
                        IR na faixa de <span class="fi-num">{{ r.ir.aliquota_pct }}</span
                        >%
                      </td>
                      <td class="num text-down">−R$ {{ r.ir.valor_ir | number: '1.2-2' }}</td>
                    </tr>
                  }
                  <tr>
                    <td class="fi-label text-ink">
                      Líquido em <span class="fi-num">{{ r.prazo_meses }}</span> meses
                    </td>
                    <td class="num fi-metric-sm" [class.text-brand]="r.melhor_opcao">
                      R$ {{ r.valor_liquido | number: '1.2-2' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          }
        </div>
      </div>
    }
  `,
})
export class FixedIncomeComponent implements OnInit {
  private api = inject(RecommendService);
  readonly loading = inject(LoadingService);
  private fb = inject(FormBuilder);
  readonly ui = inject(UiHelperService);

  rfResult = signal<RendaFixaCompareResponse | null>(null);
  referenceRates = signal<ReferenceRates | null>(null);

  rfForms!: FormArray<FormGroup<RendaFixaForm>>;

  ngOnInit(): void {
    this.rfForms = this.fb.array<FormGroup<RendaFixaForm>>([this._makeRFGroup()]);
    this.api
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
    const rates = this.referenceRates();
    this.api
      .compareRendaFixa({
        ativos,
        cdi_anual: rates?.cdi_anual ?? null,
        selic_anual: rates?.selic_anual ?? null,
        ipca_anual: rates?.ipca_anual ?? null,
      })
      .subscribe({
        next: r => this.rfResult.set(r),
        error: () => {},
      });
  }

  rateKindAt(i: number): string {
    return this.rfForms.controls[i]?.getRawValue().tipo_taxa ?? '';
  }

  contractedRateAt(i: number): number | null {
    const v = this.rfForms.controls[i]?.getRawValue();
    if (!v) return null;
    return v.tipo_taxa === 'pos_fixado' ? (v.percentual_cdi ?? null) : v.taxa;
  }

  rfTipoLabel(tipo: string): string {
    return this.ui.fixedIncomeTypeLabel(tipo);
  }
}
