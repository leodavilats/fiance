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
} from '../../../core';

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
  selector: 'app-renda-fixa',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  templateUrl: './renda-fixa.component.html',
})
export class RendaFixaComponent implements OnInit {
  private api = inject(RecommendService);
  readonly loading = inject(LoadingService);
  private fb = inject(FormBuilder);

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
    // IPCA passa a ser enviado: sem ele o backend não conseguia compor a taxa
    // real dos indexados (um IPCA+6% rendia 6%, sem inflação).
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
}
