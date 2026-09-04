import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import {
  ALLOCATION_CATEGORIES,
  AllocationCategory,
  DensityService,
  OpportunitiesFrequency,
  RecommendService,
  RiskProfile,
  UiHelperService,
} from '../../core';
import { PageHeaderComponent } from '../page-header/page-header.component';

const FREQUENCY_OPTIONS: { key: OpportunitiesFrequency; label: string }[] = [
  { key: 'off', label: 'Desativado' },
  { key: 'daily', label: 'Diária' },
  { key: 'weekly', label: 'Semanal' },
  { key: 'monthly', label: 'Mensal' },
];

const RISK_PROFILE_OPTIONS: { key: RiskProfile; label: string }[] = [
  { key: 'conservative', label: 'Conservador' },
  { key: 'moderate', label: 'Moderado' },
  { key: 'aggressive', label: 'Arrojado' },
];

@Component({
  selector: 'app-preferencias',
  standalone: true,
  imports: [PageHeaderComponent, CommonModule, ReactiveFormsModule, LucideAngularModule],
  templateUrl: './preferencias.component.html',
})
export class PreferenciasComponent implements OnInit {
  readonly densidade = inject(DensityService);
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(RecommendService);
  private readonly cdr = inject(ChangeDetectorRef);
  readonly ui = inject(UiHelperService);

  readonly categories = ALLOCATION_CATEGORIES;
  readonly frequencyOptions = FREQUENCY_OPTIONS;
  readonly riskProfileOptions = RISK_PROFILE_OPTIONS;

  readonly saving = signal(false);
  readonly message = signal('');

  readonly pushEnabled = signal(false);
  readonly registeredDevices = signal(0);

  private readonly yieldValidators = [Validators.min(0.5), Validators.max(30)];

  readonly form = this.fb.group({
    yield_stock: this.fb.control(6, { nonNullable: true, validators: this.yieldValidators }),
    yield_fii: this.fb.control(10, { nonNullable: true, validators: this.yieldValidators }),
    yield_bdr: this.fb.control(4, { nonNullable: true, validators: this.yieldValidators }),
    yield_etf: this.fb.control(4, { nonNullable: true, validators: this.yieldValidators }),
    notify_price_alerts: this.fb.control(true, { nonNullable: true }),
    opportunities_frequency: this.fb.control<OpportunitiesFrequency>('weekly', {
      nonNullable: true,
    }),
    risk_profile: this.fb.control<RiskProfile>('moderate', { nonNullable: true }),
    preferred_categories: this.fb.control<AllocationCategory[]>([], { nonNullable: true }),
    preferred_sectors: this.fb.control('', { nonNullable: true }),
    excluded_tickers: this.fb.control('', { nonNullable: true }),
  });

  ngOnInit(): void {
    this.svc.getPreferences().subscribe({
      next: prefs => {
        this.pushEnabled.set(prefs.push_enabled ?? false);
        this.registeredDevices.set(prefs.registered_devices ?? 0);
        this.form.patchValue({
          yield_stock: Math.round((prefs.desired_yield_stock ?? 0.06) * 1000) / 10,
          yield_fii: Math.round((prefs.desired_yield_fii ?? 0.1) * 1000) / 10,
          yield_bdr: Math.round((prefs.desired_yield_bdr ?? 0.04) * 1000) / 10,
          yield_etf: Math.round((prefs.desired_yield_etf ?? 0.04) * 1000) / 10,
          notify_price_alerts: prefs.notify_price_alerts ?? true,
          opportunities_frequency: prefs.opportunities_frequency ?? 'weekly',
          risk_profile: prefs.risk_profile ?? 'moderate',
          preferred_categories: prefs.preferred_categories ?? [],
          preferred_sectors: (prefs.preferred_sectors ?? []).join(', '),
          excluded_tickers: (prefs.excluded_tickers ?? []).join(', '),
        });
        this.cdr.detectChanges();
      },
      error: () => {},
    });
  }

  isPreferredCategory(cat: AllocationCategory): boolean {
    return this.form.controls.preferred_categories.value.includes(cat);
  }

  togglePreferredCategory(cat: AllocationCategory, checked: boolean): void {
    const current = this.form.controls.preferred_categories.value;
    this.form.controls.preferred_categories.setValue(
      checked ? [...current, cat] : current.filter(c => c !== cat)
    );
  }

  savePreferencias(): void {
    const v = this.form.getRawValue();
    this.saving.set(true);
    this.message.set('');

    this.svc
      .savePreferences({
        desired_yield_stock: v.yield_stock / 100,
        desired_yield_fii: v.yield_fii / 100,
        desired_yield_bdr: v.yield_bdr / 100,
        desired_yield_etf: v.yield_etf / 100,
        notify_price_alerts: v.notify_price_alerts,
        opportunities_frequency: v.opportunities_frequency,
        risk_profile: v.risk_profile,
        preferred_categories: v.preferred_categories,
        preferred_sectors: v.preferred_sectors
          .split(',')
          .map(s => s.trim())
          .filter(Boolean),
        excluded_tickers: v.excluded_tickers
          .split(',')
          .map(s => s.trim().toUpperCase())
          .filter(Boolean),
      })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.message.set('✓ Preferências salvas');
          setTimeout(() => this.message.set(''), 3000);
        },
        error: () => {
          this.saving.set(false);
          this.message.set('✗ Não conseguimos salvar suas preferências');
          setTimeout(() => this.message.set(''), 4000);
        },
      });
  }
}
