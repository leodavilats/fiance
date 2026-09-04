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
import { PriceAlert, RecommendService, TickerSuggestion } from '../../core';
import { PageHeaderComponent } from '../page-header/page-header.component';

@Component({
  selector: 'app-alertas',
  standalone: true,
  imports: [PageHeaderComponent, CommonModule, ReactiveFormsModule, LucideAngularModule],
  templateUrl: './alertas.component.html',
})
export class AlertasComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(RecommendService);
  private readonly route = inject(ActivatedRoute);

  private readonly destroy$ = new Subject<void>();
  private readonly tickerSearch$ = new Subject<string>();

  readonly alerts = signal<PriceAlert[]>([]);
  readonly alertMessage = signal('');
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
    this.svc.getAlerts().subscribe({ next: a => this.alerts.set(a), error: () => {} });
  }

  addAlert(): void {
    if (this.alertForm.invalid) return;
    const { ticker, condition, target_price, note } = this.alertForm.getRawValue();
    this.svc.createAlert({ ticker, condition, target_price, note: note || undefined }).subscribe({
      next: () => {
        this.alertForm.patchValue({ ticker: '', target_price: 0, note: '' });
        this.closeAlertTickerSuggestions();
        this.loadAlerts();
      },
      error: () => this.alertMessage.set('✗ Não conseguimos criar o alerta'),
    });
  }

  removeAlert(id: number): void {
    this.svc.deleteAlert(id).subscribe({ next: () => this.loadAlerts(), error: () => {} });
  }
}
