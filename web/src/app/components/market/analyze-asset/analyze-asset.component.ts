import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import {
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime, switchMap, takeUntil } from 'rxjs/operators';
import {
  AssetAnalysis,
  LoadingService,
  RecommendService,
  TickerSuggestion,
  UiHelperService,
} from '../../../core';

interface AnalyzeForm {
  symbol: FormControl<string>;
}

@Component({
  selector: 'app-analyze-asset',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  templateUrl: './analyze-asset.component.html',
})
export class AnalyzeAssetComponent implements OnInit, OnDestroy {
  private api = inject(RecommendService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);
  private fb = inject(FormBuilder);

  private destroy$ = new Subject<void>();

  analyzeResult = signal<AssetAnalysis | null>(null);

  analyzeForm: FormGroup<AnalyzeForm> = this.fb.group({
    symbol: this.fb.control('VALE3', { nonNullable: true, validators: Validators.required }),
  });

  symbolSuggestions = signal<TickerSuggestion[]>([]);
  symbolSuggestionsOpen = signal(false);
  private symbolSearch$ = new Subject<string>();

  ngOnInit() {
    this.symbolSearch$
      .pipe(
        debounceTime(250),
        switchMap(query => {
          if (query.trim().length < 1) return [[] as TickerSuggestion[]];
          return this.api.searchTickers(query).pipe(switchMap(res => [res.items]));
        }),
        takeUntil(this.destroy$)
      )
      .subscribe(items => {
        this.symbolSuggestions.set(items);
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onSymbolInput(value: string): void {
    this.symbolSuggestionsOpen.set(true);
    this.symbolSearch$.next(value);
  }

  selectSymbolSuggestion(suggestion: TickerSuggestion): void {
    this.analyzeForm.controls.symbol.setValue(suggestion.ticker);
    this.closeSymbolSuggestions();
  }

  closeSymbolSuggestions(): void {
    this.symbolSuggestionsOpen.set(false);
    this.symbolSuggestions.set([]);
  }

  submitAnalyze(): void {
    if (this.analyzeForm.invalid) return;
    const { symbol } = this.analyzeForm.getRawValue();
    this.api.analyzeAsset(symbol).subscribe({
      next: res => this.analyzeResult.set(res),
      error: () => {},
    });
  }
}
