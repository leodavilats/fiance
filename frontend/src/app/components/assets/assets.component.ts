import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormControl,
  FormArray,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import {
  LoadingService,
  PortfolioItem,
  PortfolioEvaluationResponse,
  PortfolioCategory,
  RecommendService,
  RendaFixaTipo,
  UiHelperService,
} from '../../core';

interface PortfolioItemForm {
  ticker: FormControl<string>;
  quantity: FormControl<number>;
  avg_price: FormControl<number>;
  category: FormControl<PortfolioCategory>;
}

interface RendaFixaItemForm {
  nome: FormControl<string>;
  tipo: FormControl<RendaFixaTipo>;
  valor_investido: FormControl<number>;
  taxa: FormControl<number>;
  prazo_meses: FormControl<number>;
  data_aplicacao: FormControl<string>;
  tipo_taxa: FormControl<'pre_fixado' | 'pos_fixado' | 'hibrido'>;
  percentual_cdi: FormControl<number | null>;
}

interface PortfolioFormShape {
  items: FormArray<FormGroup<PortfolioItemForm>>;
  renda_fixa: FormArray<FormGroup<RendaFixaItemForm>>;
  desired_yield: FormControl<number>;
}

@Component({
  selector: 'app-assets',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  templateUrl: './assets.component.html',
  styleUrls: ['./assets.component.scss'],
})
export class AssetsComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(RecommendService);
  readonly loading = inject(LoadingService);
  readonly ui = inject(UiHelperService);

  form!: FormGroup<PortfolioFormShape>;

  result = signal<PortfolioEvaluationResponse | null>(null);
  saveState = signal<'idle' | 'saving' | 'saved' | 'error'>('idle');

  expandedSections = {
    negociados: true,
    rendaFixa: true,
    avaliacao: true,
  };

  private saveDebounce = new Subject<void>();

  get portfolioItems() {
    return this.form.controls.items as FormArray<FormGroup<PortfolioItemForm>>;
  }

  get rendaFixaItems() {
    return this.form.controls.renda_fixa as FormArray<FormGroup<RendaFixaItemForm>>;
  }

  // Computed properties
  totalInvestido = computed(() => {
    const negociados = this.portfolioItems
      .getRawValue()
      .filter(x => x.ticker.trim() !== '')
      .reduce((sum, item) => sum + item.quantity * item.avg_price, 0);
    const rf = this.totalRendaFixa();
    return negociados + rf;
  });

  valorAtual = computed(() => {
    const r = this.result();
    if (!r) return this.totalInvestido();
    const negociados = r.total_current || 0;
    const rf = this.totalValorAtualRF();
    return negociados + rf;
  });

  rendimentoTotal = computed(() => {
    return this.valorAtual() - this.totalInvestido();
  });

  rendimentoPct = computed(() => {
    const invested = this.totalInvestido();
    if (invested === 0) return 0;
    return (this.rendimentoTotal() / invested) * 100;
  });

  totalAtivos = computed(() => {
    return this.portfolioItems.length + this.rendaFixaItems.length;
  });

  totalRendaFixa = computed(() => {
    return this.rendaFixaItems
      .getRawValue()
      .reduce((sum, item) => sum + (item.valor_investido || 0), 0);
  });

  totalRendimentoRF = computed(() => {
    let total = 0;
    for (let i = 0; i < this.rendaFixaItems.length; i++) {
      total += this.calcularRendimento(i);
    }
    return total;
  });

  totalValorAtualRF = computed(() => {
    return this.totalRendaFixa() + this.totalRendimentoRF();
  });

  totalValorFuturoRF = computed(() => {
    let total = 0;
    for (let i = 0; i < this.rendaFixaItems.length; i++) {
      total += this.calcularValorFinal(i);
    }
    return total;
  });

  avgTaxaRF = computed(() => {
    const items = this.rendaFixaItems.getRawValue();
    if (items.length === 0) return 0;

    // Média ponderada pelo valor investido
    let somaValorTaxa = 0;
    let somaValor = 0;

    items.forEach(item => {
      const taxa =
        item.tipo_taxa === 'pos_fixado'
          ? (item.percentual_cdi || 0) * 0.135 // Estimativa: 110% CDI ≈ 13.5% a.a. (CDI atual ~13.5%)
          : item.taxa;
      somaValorTaxa += item.valor_investido * taxa;
      somaValor += item.valor_investido;
    });

    return somaValor > 0 ? somaValorTaxa / somaValor : 0;
  });

  ngOnInit() {
    this.buildForm();
    this.loadStoredRendaFixa();
    this.saveDebounce.pipe(debounceTime(1000)).subscribe(() => this.savePortfolio());
  }

  buildForm() {
    this.form = this.fb.group<PortfolioFormShape>({
      items: this.fb.array<FormGroup<PortfolioItemForm>>([]),
      renda_fixa: this.fb.array<FormGroup<RendaFixaItemForm>>([]),
      desired_yield: this.fb.control(12, { nonNullable: true }),
    });

    this.addItem();
  }

  addItem() {
    const group = this.fb.group<PortfolioItemForm>({
      ticker: this.fb.control('', { nonNullable: true }),
      quantity: this.fb.control(0, { nonNullable: true }),
      avg_price: this.fb.control(0, { nonNullable: true }),
      category: this.fb.control('auto' as PortfolioCategory, { nonNullable: true }),
    });
    this.portfolioItems.push(group);
  }

  removeItem(index: number) {
    this.portfolioItems.removeAt(index);
    this.saveDebounce.next();
  }

  addRF() {
    const group = this.fb.group<RendaFixaItemForm>({
      nome: this.fb.control('', { nonNullable: true, validators: Validators.required }),
      tipo: this.fb.control('cdb', { nonNullable: true }),
      valor_investido: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(1)],
      }),
      taxa: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(0)],
      }),
      prazo_meses: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(1)],
      }),
      data_aplicacao: this.fb.control('', { nonNullable: true, validators: Validators.required }),
      tipo_taxa: this.fb.control('pre_fixado' as const, { nonNullable: true }),
      percentual_cdi: this.fb.control<number | null>(null),
    });
    this.rendaFixaItems.push(group);
  }

  removeRF(index: number) {
    this.rendaFixaItems.removeAt(index);
    this.saveDebounce.next();
  }

  toggleSection(section: 'negociados' | 'rendaFixa' | 'avaliacao') {
    this.expandedSections[section] = !this.expandedSections[section];
  }

  async evaluateAssets() {
    const items = this.portfolioItems.getRawValue().filter(x => x.ticker.trim() !== '');
    if (items.length === 0) return;

    this.loading.show();
    this.svc
      .evaluatePortfolio({
        items,
        desired_yield: this.form.controls.desired_yield.value,
      })
      .subscribe({
        next: res => {
          this.result.set(res);
          this.loading.hide();
        },
        error: err => {
          console.error('Erro ao avaliar portfolio:', err);
          this.loading.hide();
        },
      });
  }

  async savePortfolio() {
    const items = this.portfolioItems.getRawValue().filter(x => x.ticker.trim() !== '');

    // Converte renda fixa para PortfolioItem
    const rfItems = this.rendaFixaItems.getRawValue();
    const rfPositions: PortfolioItem[] = rfItems.map((rf, idx) => ({
      ticker: `RF_${rf.tipo}_${idx + 1}`, // Ex: RF_cdb_1, RF_tesouro_2
      quantity: 1,
      avg_price: rf.valor_investido, // O preço médio é o valor investido
      category: 'renda_fixa', // Força categoria renda_fixa
    }));

    const allItems = [...items, ...rfPositions];
    if (allItems.length === 0) return;

    this.saveState.set('saving');
    this.svc.savePortfolio(allItems).subscribe({
      next: () => {
        this.saveState.set('saved');
        // Também persiste renda fixa no localStorage para edição
        this.persistRendaFixa();
        setTimeout(() => this.saveState.set('idle'), 2000);
      },
      error: () => {
        this.saveState.set('error');
        setTimeout(() => this.saveState.set('idle'), 3000);
      },
      complete: () => {},
    });
  }

  rfTipoLabel(tipo: RendaFixaTipo): string {
    const labels: Record<RendaFixaTipo, string> = {
      cdb: 'CDB',
      lci: 'LCI',
      lca: 'LCA',
      tesouro_selic: 'Tesouro Selic',
      tesouro_ipca: 'Tesouro IPCA+',
      tesouro_pre: 'Tesouro Pré',
      lc: 'LC',
      cri: 'CRI',
      cra: 'CRA',
    };
    return labels[tipo] || tipo;
  }

  isIsentoIR(tipo: RendaFixaTipo): boolean {
    return ['lci', 'lca', 'cri', 'cra'].includes(tipo);
  }

  calcularRendimento(index: number): number {
    const item = this.rendaFixaItems.at(index)?.getRawValue();
    if (!item) return 0;

    const CDI_ANUAL = 13.5; // Taxa CDI estimada 13.5% a.a.

    let taxaAnual = 0;
    if (item.tipo_taxa === 'pos_fixado') {
      taxaAnual = ((item.percentual_cdi || 100) / 100) * CDI_ANUAL;
    } else {
      taxaAnual = item.taxa;
    }

    // Calcular dias corridos desde a aplicação
    const dataAplicacao = new Date(item.data_aplicacao);
    const hoje = new Date();
    const diasCorridos = Math.max(
      0,
      Math.floor((hoje.getTime() - dataAplicacao.getTime()) / (1000 * 60 * 60 * 24))
    );

    // Rendimento proporcional ao período
    const rendimentoBruto =
      item.valor_investido * (Math.pow(1 + taxaAnual / 100, diasCorridos / 365) - 1);

    // Aplicar IR se não for isento
    if (this.isIsentoIR(item.tipo)) {
      return rendimentoBruto;
    }

    // Alíquota de IR regressiva
    let aliquotaIR = 0.225; // 22,5% até 180 dias
    if (diasCorridos > 720)
      aliquotaIR = 0.15; // 15% acima de 720 dias
    else if (diasCorridos > 360)
      aliquotaIR = 0.175; // 17,5% de 361 a 720 dias
    else if (diasCorridos > 180) aliquotaIR = 0.2; // 20% de 181 a 360 dias

    return rendimentoBruto * (1 - aliquotaIR);
  }

  calcularValorFinal(index: number): number {
    const item = this.rendaFixaItems.at(index)?.getRawValue();
    if (!item) return 0;

    const CDI_ANUAL = 13.5;

    let taxaAnual = 0;
    if (item.tipo_taxa === 'pos_fixado') {
      taxaAnual = ((item.percentual_cdi || 100) / 100) * CDI_ANUAL;
    } else {
      taxaAnual = item.taxa;
    }

    // Montante no vencimento
    const montanteBruto =
      item.valor_investido * Math.pow(1 + taxaAnual / 100, item.prazo_meses / 12);
    const rendimentoBruto = montanteBruto - item.valor_investido;

    // Aplicar IR
    if (this.isIsentoIR(item.tipo)) {
      return montanteBruto;
    }

    // Alíquota de IR para o prazo total
    const diasTotais = item.prazo_meses * 30;
    let aliquotaIR = 0.225;
    if (diasTotais > 720) aliquotaIR = 0.15;
    else if (diasTotais > 360) aliquotaIR = 0.175;
    else if (diasTotais > 180) aliquotaIR = 0.2;

    return item.valor_investido + rendimentoBruto * (1 - aliquotaIR);
  }

  private loadStoredRendaFixa(): void {
    const stored = localStorage.getItem('portfolio_renda_fixa');
    if (!stored) return;

    try {
      const items = JSON.parse(stored);
      items.forEach((item: any) => {
        const group = this.fb.group<RendaFixaItemForm>({
          nome: this.fb.control(item.nome || '', {
            nonNullable: true,
            validators: Validators.required,
          }),
          tipo: this.fb.control(item.tipo || 'cdb', { nonNullable: true }),
          valor_investido: this.fb.control(item.valor_investido || 0, {
            nonNullable: true,
            validators: [Validators.required, Validators.min(1)],
          }),
          taxa: this.fb.control(item.taxa || 0, {
            nonNullable: true,
            validators: [Validators.required, Validators.min(0)],
          }),
          prazo_meses: this.fb.control(item.prazo_meses || 0, {
            nonNullable: true,
            validators: [Validators.required, Validators.min(1)],
          }),
          data_aplicacao: this.fb.control(item.data_aplicacao || '', {
            nonNullable: true,
            validators: Validators.required,
          }),
          tipo_taxa: this.fb.control(item.tipo_taxa || 'pre_fixado', { nonNullable: true }),
          percentual_cdi: this.fb.control(item.percentual_cdi || null),
        });
        this.rendaFixaItems.push(group);
      });
    } catch (e) {
      console.error('Erro ao carregar renda fixa:', e);
    }
  }

  private persistRendaFixa(): void {
    const items = this.rendaFixaItems.getRawValue();
    localStorage.setItem('portfolio_renda_fixa', JSON.stringify(items));
  }
}
