import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime, switchMap } from 'rxjs/operators';
import {
  FixedIncomePayload,
  FixedIncomePosition,
  LoadingService,
  RecommendService,
  RendaFixaTipo,
  SnackbarService,
  StoredPortfolioItem,
  TickerSuggestion,
} from '../../core';

type RowState = 'idle' | 'saving' | 'saved' | 'error';

interface AssetRow {
  savedTicker: string | null;
  state: RowState;
  error: string | null;
}

/** "Meus Ativos" — **cadastro**. */
@Component({
  selector: 'app-portfolio-editor',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule, RouterLink],
  templateUrl: './portfolio-editor.component.html',
})
export class PortfolioEditorComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(RecommendService);
  private readonly snackbar = inject(SnackbarService);
  readonly loading = inject(LoadingService);

  assetForms = signal<FormGroup[]>([]);
  assetMeta = signal<AssetRow[]>([]);
  assetsLoaded = signal(false);
  loadFailed = signal(false);

  tickerSuggestions = signal<TickerSuggestion[]>([]);
  tickerSuggestionsRow = signal<number | null>(null);
  private tickerSearch$ = new Subject<{ index: number; query: string }>();

  fixedIncome = signal<FixedIncomePosition[]>([]);
  fixedIncomeForm!: FormGroup;
  editingFixedIncomeId = signal<number | null>(null);
  savingFixedIncome = signal(false);

  readonly rendaFixaTipos: { value: RendaFixaTipo; label: string }[] = [
    { value: 'cdb', label: 'CDB' },
    { value: 'lci', label: 'LCI (isento de IR)' },
    { value: 'lca', label: 'LCA (isento de IR)' },
    { value: 'lc', label: 'LC' },
    { value: 'cri', label: 'CRI (isento de IR)' },
    { value: 'cra', label: 'CRA (isento de IR)' },
    { value: 'tesouro_selic', label: 'Tesouro Selic' },
    { value: 'tesouro_ipca', label: 'Tesouro IPCA+' },
    { value: 'tesouro_pre', label: 'Tesouro Pré' },
  ];

  isPosFixado = computed(() => this.fixedIncomeForm?.get('tipo_taxa')?.value === 'pos_fixado');

  ngOnInit(): void {
    this.buildFixedIncomeForm();
    this.loadAssets();
    this.loadFixedIncome();

    this.tickerSearch$
      .pipe(
        debounceTime(250),
        switchMap(({ index, query }) => {
          if (query.trim().length < 1) return [{ index, items: [] as TickerSuggestion[] }];
          return this.svc
            .searchTickers(query)
            .pipe(switchMap(res => [{ index, items: res.items }]));
        })
      )
      .subscribe(({ index, items }) => {
        if (this.tickerSuggestionsRow() !== index) return;
        this.tickerSuggestions.set(items);
      });
  }

  private newAssetForm(item?: StoredPortfolioItem): FormGroup {
    return this.fb.group({
      ticker: this.fb.control(item?.ticker ?? '', {
        nonNullable: true,
        validators: [Validators.required, Validators.pattern(/^[A-Za-z][A-Za-z0-9]{3}\d{1,2}$/)],
      }),
      quantity: this.fb.control(item?.quantity ?? 0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(0.000001)],
      }),
      avg_price: this.fb.control(item?.avg_price ?? 0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(0.01)],
      }),
    });
  }

  private loadAssets(): void {
    this.svc.getPortfolio().subscribe({
      next: res => {
        this.assetForms.set(res.items.map(i => this.newAssetForm(i)));
        this.assetMeta.set(
          res.items.map(i => ({ savedTicker: i.ticker, state: 'idle' as RowState, error: null }))
        );
        this.assetsLoaded.set(true);
      },
      error: () => {
        this.loadFailed.set(true);
      },
    });
  }

  reload(): void {
    this.loadFailed.set(false);
    this.assetsLoaded.set(false);
    this.loadAssets();
    this.loadFixedIncome();
  }

  addAssetRow(): void {
    this.assetForms.update(forms => [...forms, this.newAssetForm()]);
    this.assetMeta.update(meta => [...meta, { savedTicker: null, state: 'idle', error: null }]);
  }

  private patchMeta(index: number, patch: Partial<AssetRow>): void {
    this.assetMeta.update(meta => meta.map((m, i) => (i === index ? { ...m, ...patch } : m)));
  }

  saveAssetRow(index: number): void {
    const form = this.assetForms()[index];
    if (!form) return;

    if (form.invalid) {
      form.markAllAsTouched();
      this.patchMeta(index, {
        state: 'error',
        error: 'Preencha ticker (ex.: PETR4), quantidade e preço médio.',
      });
      return;
    }

    const value = form.getRawValue() as { ticker: string; quantity: number; avg_price: number };
    const ticker = value.ticker.trim().toUpperCase();
    const previous = this.assetMeta()[index]?.savedTicker;

    this.patchMeta(index, { state: 'saving', error: null });

    this.svc
      .upsertPosition({ ticker, quantity: value.quantity, avg_price: value.avg_price })
      .subscribe({
        next: () => {
          if (previous && previous !== ticker) {
            this.svc.deletePosition(previous).subscribe({ error: () => {} });
          }
          this.patchMeta(index, { savedTicker: ticker, state: 'saved', error: null });
          setTimeout(() => this.patchMeta(index, { state: 'idle' }), 2000);
        },
        error: err => {
          this.patchMeta(index, {
            state: 'error',
            error: err?.error?.detail || 'Não foi possível salvar esta linha.',
          });
        },
      });
  }

  removeAssetRow(index: number): void {
    const meta = this.assetMeta()[index];

    const dropRow = () => {
      this.assetForms.update(forms => forms.filter((_, i) => i !== index));
      this.assetMeta.update(m => m.filter((_, i) => i !== index));
    };

    if (!meta?.savedTicker) {
      dropRow();
      return;
    }

    this.patchMeta(index, { state: 'saving', error: null });
    this.svc.deletePosition(meta.savedTicker).subscribe({
      next: () => {
        dropRow();
        this.snackbar.showSuccess(`${meta.savedTicker} removido da carteira.`);
      },
      error: () =>
        this.patchMeta(index, { state: 'error', error: 'Não foi possível remover esta posição.' }),
    });
  }

  onTickerInput(index: number, value: string): void {
    this.tickerSuggestionsRow.set(index);
    this.tickerSearch$.next({ index, query: value });
  }

  selectTickerSuggestion(index: number, suggestion: TickerSuggestion): void {
    this.assetForms()[index]?.get('ticker')?.setValue(suggestion.ticker);
    this.closeTickerSuggestions();
  }

  closeTickerSuggestions(): void {
    this.tickerSuggestionsRow.set(null);
    this.tickerSuggestions.set([]);
  }

  assetRowState(index: number): RowState {
    return this.assetMeta()[index]?.state ?? 'idle';
  }

  assetRowError(index: number): string | null {
    return this.assetMeta()[index]?.error ?? null;
  }

  private buildFixedIncomeForm(position?: FixedIncomePosition): void {
    this.fixedIncomeForm = this.fb.group({
      nome: this.fb.control(position?.nome ?? '', {
        nonNullable: true,
        validators: [Validators.required, Validators.maxLength(120)],
      }),
      tipo: this.fb.control<RendaFixaTipo>(position?.tipo ?? 'cdb', { nonNullable: true }),
      valor_investido: this.fb.control(position?.valor_investido ?? 0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(0.01)],
      }),
      tipo_taxa: this.fb.control(position?.tipo_taxa ?? 'pre_fixado', { nonNullable: true }),
      taxa: this.fb.control(position?.taxa ?? 0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(0.01)],
      }),
      percentual_cdi: this.fb.control<number | null>(position?.percentual_cdi ?? null),
      data_aplicacao: this.fb.control(position?.data_aplicacao ?? '', {
        nonNullable: true,
        validators: [Validators.required],
      }),
      vencimento: this.fb.control<string | null>(position?.vencimento ?? null),
      liquidez: this.fb.control(position?.liquidez ?? 'no_vencimento', { nonNullable: true }),
      oculto: this.fb.control(position?.oculto ?? false, { nonNullable: true }),
    });
  }

  private loadFixedIncome(): void {
    this.svc.getFixedIncome().subscribe({
      next: res => this.fixedIncome.set(res.items),
      error: () => this.loadFailed.set(true),
    });
  }

  startNewFixedIncome(): void {
    this.editingFixedIncomeId.set(null);
    this.buildFixedIncomeForm();
  }

  editFixedIncome(position: FixedIncomePosition): void {
    this.editingFixedIncomeId.set(position.id);
    this.buildFixedIncomeForm(position);
  }

  saveFixedIncome(): void {
    if (this.fixedIncomeForm.invalid) {
      this.fixedIncomeForm.markAllAsTouched();
      this.snackbar.showError('Preencha nome, valor, taxa e data de aplicação.');
      return;
    }

    const raw = this.fixedIncomeForm.getRawValue();
    const payload: FixedIncomePayload = {
      nome: raw.nome,
      tipo: raw.tipo,
      valor_investido: raw.valor_investido,
      taxa: raw.taxa,
      tipo_taxa: raw.tipo_taxa,
      percentual_cdi: raw.tipo_taxa === 'pos_fixado' ? raw.percentual_cdi : null,
      data_aplicacao: raw.data_aplicacao,
      vencimento: raw.vencimento || null,
      liquidez: raw.liquidez,
      oculto: raw.oculto,
    };

    this.savingFixedIncome.set(true);
    const editingId = this.editingFixedIncomeId();
    const request = editingId
      ? this.svc.updateFixedIncome(editingId, payload)
      : this.svc.createFixedIncome(payload);

    request.subscribe({
      next: () => {
        this.savingFixedIncome.set(false);
        this.snackbar.showSuccess(editingId ? 'Aplicação atualizada.' : 'Aplicação cadastrada.');
        this.startNewFixedIncome();
        this.loadFixedIncome();
      },
      error: err => {
        this.savingFixedIncome.set(false);
        this.snackbar.showError(err?.error?.detail || 'Não foi possível salvar a aplicação.');
      },
    });
  }

  cancelFixedIncomeEdit(): void {
    this.startNewFixedIncome();
  }

  deleteFixedIncome(position: FixedIncomePosition): void {
    this.svc.deleteFixedIncome(position.id).subscribe({
      next: () => {
        this.snackbar.showSuccess(`${position.nome} removido.`);
        if (this.editingFixedIncomeId() === position.id) this.startNewFixedIncome();
        this.loadFixedIncome();
      },
      error: () => this.snackbar.showError('Não foi possível remover a aplicação.'),
    });
  }

  toggleFixedIncomeHidden(position: FixedIncomePosition): void {
    this.svc.updateFixedIncome(position.id, { oculto: !position.oculto }).subscribe({
      next: () => this.loadFixedIncome(),
      error: () => this.snackbar.showError('Não foi possível atualizar a aplicação.'),
    });
  }

  rfTipoLabel(tipo: RendaFixaTipo | string): string {
    return this.rendaFixaTipos.find(t => t.value === tipo)?.label ?? tipo;
  }

  trackFixedIncome(_: number, item: FixedIncomePosition): number {
    return item.id;
  }
}
