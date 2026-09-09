import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import {
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime, switchMap, takeUntil } from 'rxjs/operators';
import { PriceAlert, RecommendService, TickerSuggestion, mensagemDeErro } from '../../core';
import { AsyncStateComponent } from '../async-state/async-state.component';
import { PageHeaderComponent } from '../page-header/page-header.component';

@Component({
  selector: 'app-price-alerts',
  standalone: true,
  imports: [
    PageHeaderComponent,
    CommonModule,
    ReactiveFormsModule,
    LucideAngularModule,
    AsyncStateComponent,
  ],
  template: `
    <div class="fi-block">
      <app-page-header
        title="Alertas de preço"
        question="Ao abrir o app, um aviso aparece se algum ativo atingir a condição que você definiu."
      />

      <form [formGroup]="alertForm" (ngSubmit)="addAlert()" class="flex flex-col gap-3 mb-4">
        <div class="relative flex-1 min-w-[120px]">
          <input
            formControlName="ticker"
            type="text"
            placeholder="Ticker (ex: PETR4)"
            class="input w-full"
            style="text-transform: uppercase"
            autocomplete="off"
            (input)="onAlertTickerInput($any($event.target).value)"
            (focus)="onAlertTickerInput($any($event.target).value)"
            (focusout)="closeAlertTickerSuggestions()"
          />
          @if (alertTickerSuggestionsOpen() && alertTickerSuggestions().length > 0) {
            <ul
              class="fi-body absolute top-full left-0 right-0 mt-1 z-popover rounded-lg border border-hairline bg-ground-1 shadow-popover max-h-56 overflow-y-auto"
            >
              @for (s of alertTickerSuggestions(); track s.ticker) {
                <li>
                  <button
                    type="button"
                    class="menu-item justify-between"
                    (mousedown)="$event.preventDefault(); selectAlertTickerSuggestion(s)"
                  >
                    <span class="fi-label text-ink">{{ s.ticker }}</span>
                    <span class="fi-caption text-ink-2 truncate">{{ s.name }}</span>
                  </button>
                </li>
              }
            </ul>
          }
        </div>
        <select formControlName="condition" class="input w-32">
          <option value="below">Abaixo de</option>
          <option value="above">Acima de</option>
        </select>
        <input
          formControlName="target_price"
          type="number"
          step="0.01"
          min="0.01"
          placeholder="Preco alvo"
          class="input w-32"
        />
        <input
          formControlName="note"
          type="text"
          placeholder="Nota (opcional)"
          class="input flex-1 min-w-[120px]"
        />
        <button
          type="submit"
          [disabled]="alertForm.invalid"
          [title]="alertForm.invalid ? 'Informe o ticker e o preço-alvo para criar o alerta' : ''"
          class="btn-primary"
        >
          <lucide-icon name="plus" size="16"></lucide-icon> Adicionar
        </button>
      </form>

      @if (erroAoCriar(); as falha) {
        <p class="fi-body text-adverse mb-3" role="alert">{{ falha }}</p>
      }

      <app-async-state
        [loading]="carregando()"
        [error]="erro()"
        loadingShape="row"
        [loadingCount]="3"
        loadingLabel="Carregando seus alertas"
        errorTitle="Não conseguimos abrir seus alertas"
        errorAction="carregar seus alertas de preço"
        (retry)="loadAlerts()"
      >
        @if (alerts().length === 0) {
          <p class="fi-body text-ink-2">Nenhum alerta configurado.</p>
        } @else {
          <div class="flex flex-col gap-2">
            @for (a of alerts(); track a.id) {
              <div
                class="flex items-center justify-between gap-3 p-3 rounded-md border"
                [class.border-brand]="!!a.triggered_at"
                [class.border-hairline]="!a.triggered_at"
                [class.opacity-60]="!!a.triggered_at"
                style="background: var(--fi-ground-2)"
              >
                <div class="fi-body flex items-center gap-3 flex-wrap">
                  <span class="fi-label text-ink">{{ a.ticker }}</span>
                  <span
                    class="fi-label px-2 py-0.5 rounded-pill border"
                    [class.text-brand]="a.condition === 'above'"
                    [class.border-brand]="a.condition === 'above'"
                    [class.text-attention]="a.condition === 'below'"
                    [class.border-attention]="a.condition === 'below'"
                  >
                    {{ a.condition === 'below' ? 'Abaixo de' : 'Acima de' }}
                  </span>
                  <span class="fi-label text-ink">R$ {{ a.target_price | number: '1.2-2' }}</span>
                  @if (a.note) {
                    <span class="fi-caption text-ink-2">-- {{ a.note }}</span>
                  }
                  @if (a.triggered_at) {
                    <span class="fi-label text-brand">Disparado</span>
                  }
                </div>
                <button
                  type="button"
                  (click)="removeAlert(a.id)"
                  class="btn-icon btn-icon-quiet btn-icon-danger"
                  title="Remover alerta"
                  aria-label="Remover alerta"
                >
                  <lucide-icon name="trash2" size="16"></lucide-icon>
                </button>
              </div>
            }
          </div>
        }
      </app-async-state>
    </div>
  `,
})
export class PriceAlertsComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(RecommendService);
  private readonly route = inject(ActivatedRoute);

  private readonly destroy$ = new Subject<void>();
  private readonly tickerSearch$ = new Subject<string>();

  readonly alerts = signal<PriceAlert[]>([]);
  readonly erroAoCriar = signal('');
  readonly erro = signal<unknown>(null);
  readonly carregando = signal(true);
  readonly alertTickerSuggestions = signal<TickerSuggestion[]>([]);
  readonly alertTickerSuggestionsOpen = signal(false);

  readonly alertForm: FormGroup<{
    ticker: FormControl<string>;
    condition: FormControl<string>;
    target_price: FormControl<number>;
    note: FormControl<string>;
  }> = this.fb.group({
    ticker: this.fb.control('', { nonNullable: true, validators: Validators.required }),
    condition: this.fb.control('below', { nonNullable: true }),
    target_price: this.fb.control(0, { nonNullable: true, validators: Validators.min(0.01) }),
    note: this.fb.control('', { nonNullable: true }),
  });

  ngOnInit(): void {
    const ticker = this.route.snapshot.queryParamMap.get('ticker');
    if (ticker) this.alertForm.controls.ticker.setValue(ticker.toUpperCase());

    this.loadAlerts();

    this.tickerSearch$
      .pipe(
        debounceTime(250),
        switchMap(query => {
          if (query.trim().length < 1) return [[] as TickerSuggestion[]];
          return this.svc.searchTickers(query).pipe(switchMap(res => [res.items]));
        }),
        takeUntil(this.destroy$)
      )
      .subscribe(items => this.alertTickerSuggestions.set(items));
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onAlertTickerInput(value: string): void {
    this.alertTickerSuggestionsOpen.set(true);
    this.tickerSearch$.next(value);
  }

  selectAlertTickerSuggestion(suggestion: TickerSuggestion): void {
    this.alertForm.controls.ticker.setValue(suggestion.ticker);
    this.closeAlertTickerSuggestions();
  }

  closeAlertTickerSuggestions(): void {
    this.alertTickerSuggestionsOpen.set(false);
    this.alertTickerSuggestions.set([]);
  }

  loadAlerts(): void {
    this.carregando.set(true);
    this.erro.set(null);
    this.svc.getAlerts().subscribe({
      next: a => {
        this.alerts.set(a);
        this.carregando.set(false);
      },
      error: err => {
        this.erro.set(err);
        this.carregando.set(false);
      },
    });
  }

  addAlert(): void {
    if (this.alertForm.invalid) return;
    const { ticker, condition, target_price, note } = this.alertForm.getRawValue();
    this.svc.createAlert({ ticker, condition, target_price, note: note || undefined }).subscribe({
      next: () => {
        this.erroAoCriar.set('');
        this.alertForm.patchValue({ ticker: '', target_price: 0, note: '' });
        this.closeAlertTickerSuggestions();
        this.loadAlerts();
      },
      error: err => this.erroAoCriar.set(mensagemDeErro(err, 'criar este alerta')),
    });
  }

  removeAlert(id: number): void {
    this.svc.deleteAlert(id).subscribe({
      next: () => this.loadAlerts(),
      error: err => this.erroAoCriar.set(mensagemDeErro(err, 'apagar este alerta')),
    });
  }
}
