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
  UiHelperService,
} from '../../core';

type RowState = 'idle' | 'saving' | 'saved' | 'error';

interface AssetRow {
  savedTicker: string | null;
  state: RowState;
  error: string | null;
}

@Component({
  selector: 'app-portfolio-editor',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule, RouterLink],
  template: `
    <div class="flex flex-wrap items-center justify-between gap-3 mb-5">
      <div>
        <h1 class="fi-title m-0 text-ink">Cadastro da carteira</h1>
        <p class="fi-body text-ink-2 m-0 mt-1">
          Cada linha é salva quando você clica em salvar — nada é gravado enquanto você digita.
        </p>
      </div>
      <a routerLink="/carteira" class="btn-secondary">
        <lucide-icon name="arrow-left" size="14"></lucide-icon> Voltar para a carteira
      </a>
    </div>

    @if (loadFailed()) {
      <div
        class="p-4 rounded-md bg-adverse/10 border border-adverse/40 mb-5 flex items-start gap-3"
        role="alert"
      >
        <lucide-icon name="triangle-alert" size="20" class="text-adverse mt-0.5"></lucide-icon>
        <div class="flex-1">
          <div class="fi-label text-ink">Não conseguimos carregar sua carteira</div>
          <div class="fi-body text-ink-2 mt-1">
            A edição está bloqueada para não sobrescrever seus dados. Tente carregar de novo.
          </div>
        </div>
        <button type="button" class="btn-secondary compact-btn" (click)="reload()">
          Tentar de novo
        </button>
      </div>
    }

    <div class="fi-block">
      <h2 class="fi-title m-0 mb-1 text-ink">Ativos negociados</h2>
      <p class="fi-body text-ink-2 mb-4">
        Ações, FIIs, BDRs e ETFs da B3, pelo ticker (ex.: PETR4, HGLG11, AAPL34).
      </p>

      @if (!assetsLoaded() && !loadFailed()) {
        <p class="fi-body text-ink-2 italic">Carregando…</p>
      } @else if (assetsLoaded()) {
        <div class="flex flex-col gap-3">
          @for (form of assetForms(); track $index; let i = $index) {
            <div
              class="card p-3"
              [class.border-adverse]="assetRowState(i) === 'error'"
              [formGroup]="form"
            >
              <div
                class="grid grid-cols-1 sm:grid-cols-[2fr_1fr_1fr_auto_2.25rem] gap-3 sm:gap-2 sm:items-end"
              >
                <div class="relative flex flex-col gap-1">
                  <span class="fi-label text-ink-2">Ticker</span>
                  <input
                    type="text"
                    formControlName="ticker"
                    placeholder="ex.: PETR4"
                    autocomplete="off"
                    class="input uppercase"
                    (input)="onTickerInput(i, $any($event.target).value)"
                    (blur)="closeTickerSuggestions()"
                  />
                  @if (tickerSuggestionsRow() === i && tickerSuggestions().length > 0) {
                    <ul
                      class="absolute top-full left-0 right-0 z-popover mt-1 max-h-56 overflow-y-auto rounded-lg border border-hairline bg-ground-1 shadow-popover list-none p-0 m-0"
                    >
                      @for (s of tickerSuggestions(); track s.ticker) {
                        <li>
                          <button
                            type="button"
                            class="menu-item"
                            (mousedown)="selectTickerSuggestion(i, s)"
                          >
                            <span class="fi-label">{{ s.ticker }}</span>
                            <span class="fi-caption text-ink-2 ml-2">{{ s.name }}</span>
                          </button>
                        </li>
                      }
                    </ul>
                  }
                </div>

                <label class="flex flex-col gap-1">
                  <span class="fi-label text-ink-2">Quantidade</span>
                  <input
                    type="number"
                    formControlName="quantity"
                    min="0"
                    step="any"
                    class="input"
                  />
                </label>

                <label class="flex flex-col gap-1">
                  <span class="fi-label text-ink-2">Preço médio (R$)</span>
                  <input
                    type="number"
                    formControlName="avg_price"
                    min="0"
                    step="0.01"
                    class="input"
                  />
                </label>

                <button
                  type="button"
                  class="btn-primary"
                  [disabled]="assetRowState(i) === 'saving'"
                  (click)="saveAssetRow(i)"
                >
                  @switch (assetRowState(i)) {
                    @case ('saving') {
                      <lucide-icon
                        name="loader-circle"
                        size="14"
                        class="animate-spin"
                      ></lucide-icon>
                      Salvando
                    }
                    @case ('saved') {
                      <lucide-icon name="check" size="14"></lucide-icon> Salvo
                    }
                    @default {
                      <lucide-icon name="save" size="14"></lucide-icon> Salvar
                    }
                  }
                </button>

                <button
                  type="button"
                  class="btn-icon btn-icon-danger"
                  title="Remover"
                  (click)="removeAssetRow(i)"
                  aria-label="Remover posição"
                >
                  <lucide-icon name="trash-2" size="16"></lucide-icon>
                </button>
              </div>

              @if (assetRowError(i)) {
                <p class="fi-caption text-adverse mt-2 m-0">{{ assetRowError(i) }}</p>
              }
            </div>
          }
        </div>

        <button type="button" class="btn-secondary" (click)="addAssetRow()">
          <lucide-icon name="plus" size="14"></lucide-icon> Adicionar ativo
        </button>
      }
    </div>

    <div class="fi-block">
      <h2 class="fi-title m-0 mb-1 text-ink">Renda fixa</h2>
      <p class="fi-body text-ink-2 mb-4">
        CDB, LCI/LCA, Tesouro e afins. Os dados ficam na sua conta no servidor, então aparecem em
        qualquer navegador e também no app — e o rendimento é calculado pela mesma regra do
        comparador.
      </p>

      <form [formGroup]="fixedIncomeForm" class="card mb-5" (ngSubmit)="saveFixedIncome()">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <label class="flex flex-col gap-1 sm:col-span-2">
            <span class="fi-label text-ink-2">Nome / banco emissor</span>
            <input
              type="text"
              formControlName="nome"
              placeholder="ex.: CDB Banco Inter 2027"
              class="input"
            />
          </label>

          <label class="flex flex-col gap-1">
            <span class="fi-label text-ink-2">Tipo</span>
            <select formControlName="tipo" class="input">
              @for (t of rendaFixaTipos; track t.value) {
                <option [value]="t.value">{{ t.label }}</option>
              }
            </select>
          </label>

          <label class="flex flex-col gap-1">
            <span class="fi-label text-ink-2">Valor aplicado (R$)</span>
            <input
              type="number"
              formControlName="valor_investido"
              min="0"
              step="0.01"
              class="input"
            />
          </label>

          <label class="flex flex-col gap-1">
            <span class="fi-label text-ink-2">Tipo de taxa</span>
            <select formControlName="tipo_taxa" class="input">
              <option value="pre_fixado">Pré-fixado</option>
              <option value="pos_fixado">Pós-fixado (% do CDI)</option>
              <option value="hibrido">Híbrido (IPCA + taxa)</option>
            </select>
          </label>

          <label class="flex flex-col gap-1">
            <span class="fi-label text-ink-2">
              {{ isPosFixado() ? 'Taxa de referência (% a.a.)' : 'Taxa (% a.a.)' }}
            </span>
            <input type="number" formControlName="taxa" min="0" step="0.01" class="input" />
          </label>

          @if (isPosFixado()) {
            <label class="flex flex-col gap-1">
              <span class="fi-label text-ink-2">% do CDI</span>
              <input
                type="number"
                formControlName="percentual_cdi"
                min="0"
                step="1"
                placeholder="ex.: 110"
                class="input"
              />
            </label>
          }

          <label class="flex flex-col gap-1">
            <span class="fi-label text-ink-2">Data de aplicação</span>
            <input type="date" formControlName="data_aplicacao" class="input" />
          </label>

          <label class="flex flex-col gap-1">
            <span class="fi-label text-ink-2">Vencimento (opcional)</span>
            <input type="date" formControlName="vencimento" class="input" />
          </label>

          <label class="flex flex-col gap-1">
            <span class="fi-label text-ink-2">Liquidez</span>
            <select formControlName="liquidez" class="input">
              <option value="no_vencimento">No vencimento</option>
              <option value="diaria">Diária</option>
            </select>
          </label>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-3 mt-4">
          <label class="fi-body flex items-center gap-2 text-ink-2 cursor-pointer">
            <input type="checkbox" formControlName="oculto" class="accent-brand" />
            Não somar na carteira (reserva à parte)
          </label>

          <div class="flex items-center gap-2">
            @if (editingFixedIncomeId()) {
              <button type="button" class="btn-secondary" (click)="cancelFixedIncomeEdit()">
                Cancelar edição
              </button>
            }
            <button type="submit" class="btn-primary" [disabled]="savingFixedIncome()">
              <lucide-icon name="save" size="14"></lucide-icon>
              {{
                savingFixedIncome()
                  ? 'Salvando…'
                  : editingFixedIncomeId()
                    ? 'Salvar alterações'
                    : 'Adicionar aplicação'
              }}
            </button>
          </div>
        </div>
      </form>

      @if (fixedIncome().length === 0) {
        <p class="fi-body text-ink-2 italic m-0">
          Nenhuma aplicação de renda fixa cadastrada ainda.
        </p>
      } @else {
        <div style="overflow-x: auto">
          <table class="fi-body w-full border-collapse">
            <thead>
              <tr class="border-b border-hairline">
                <th class="fi-label text-left py-2 px-2 text-ink-2">Aplicação</th>
                <th class="fi-label text-left py-2 px-2 text-ink-2">Tipo</th>
                <th class="fi-label text-right py-2 px-2 text-ink-2">Aplicado</th>
                <th class="fi-label text-right py-2 px-2 text-ink-2">Taxa efetiva</th>
                <th class="fi-label text-right py-2 px-2 text-ink-2">Hoje</th>
                <th class="fi-label text-right py-2 px-2 text-ink-2"></th>
              </tr>
            </thead>
            <tbody>
              @for (item of fixedIncome(); track trackFixedIncome($index, item)) {
                <tr
                  class="border-b border-hairline hover:bg-ground-2 transition-colors"
                  [class.opacity-50]="item.oculto"
                >
                  <td class="fi-label py-2 px-2 text-ink">
                    {{ item.nome }}
                    @if (item.oculto) {
                      <span class="fi-caption ml-1 text-ink-2">(fora da carteira)</span>
                    }
                  </td>
                  <td class="py-2 px-2 text-ink-2">{{ rfTipoLabel(item.tipo) }}</td>
                  <td class="text-right py-2 px-2 text-ink">
                    {{ item.valor_investido | number: '1.2-2' }}
                  </td>
                  <td class="text-right py-2 px-2 text-ink">
                    {{ item.taxa_anual_efetiva_pct | number: '1.2-2' }}%
                  </td>
                  <td class="text-right py-2 px-2 text-ink">
                    {{ item.valor_atual | number: '1.2-2' }}
                  </td>
                  <td class="py-2 px-2">
                    <div class="flex items-center gap-1 justify-end">
                      <button
                        type="button"
                        class="btn-icon"
                        title="Editar"
                        (click)="editFixedIncome(item)"
                        aria-label="Editar posição de renda fixa"
                      >
                        <lucide-icon name="pencil" size="14"></lucide-icon>
                      </button>
                      <button
                        type="button"
                        class="btn-icon"
                        [title]="item.oculto ? 'Somar na carteira' : 'Não somar na carteira'"
                        (click)="toggleFixedIncomeHidden(item)"
                        aria-label="Mostrar ou ocultar esta posição"
                      >
                        <lucide-icon
                          [name]="item.oculto ? 'eye' : 'eye-off'"
                          size="14"
                        ></lucide-icon>
                      </button>
                      <button
                        type="button"
                        class="btn-icon btn-icon-danger"
                        title="Remover"
                        (click)="deleteFixedIncome(item)"
                        aria-label="Remover posição de renda fixa"
                      >
                        <lucide-icon name="trash-2" size="14"></lucide-icon>
                      </button>
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
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

  private static readonly ISENTOS = new Set(['lci', 'lca', 'cri', 'cra']);

  readonly rendaFixaTipos = inject(UiHelperService).fixedIncomeTypes.map(t => ({
    value: t.value as RendaFixaTipo,
    label: PortfolioEditorComponent.ISENTOS.has(t.value) ? `${t.label} (isento de IR)` : t.label,
  }));

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
