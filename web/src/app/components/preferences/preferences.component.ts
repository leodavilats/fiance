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
  selector: 'app-preferences',
  standalone: true,
  imports: [PageHeaderComponent, CommonModule, ReactiveFormsModule, LucideAngularModule],
  template: `
    <app-page-header title="Preferências" question="Como o fiance calcula, e o que ele te avisa." />

    <form [formGroup]="form" class="flex flex-col gap-8">
      <div class="fi-block">
        <h2 class="fi-title m-0 mb-4 text-ink">Como o fiance te avalia</h2>
        <label class="field-label block mb-2">
          Meta de dividend yield (preço-teto de Bazin) — por tipo de ativo
        </label>
        <div class="grid grid-cols-4 gap-4">
          <div>
            <label class="field-label block mb-1">Ações BR (%)</label>
            <input
              type="number"
              class="input"
              formControlName="yield_stock"
              min="0.5"
              max="30"
              step="0.5"
            />
          </div>
          <div>
            <label class="field-label block mb-1">FIIs (%)</label>
            <input
              type="number"
              class="input"
              formControlName="yield_fii"
              min="0.5"
              max="30"
              step="0.5"
            />
          </div>
          <div>
            <label class="field-label block mb-1">BDRs (%)</label>
            <input
              type="number"
              class="input"
              formControlName="yield_bdr"
              min="0.5"
              max="30"
              step="0.5"
            />
          </div>
          <div>
            <label class="field-label block mb-1">ETFs (%)</label>
            <input
              type="number"
              class="input"
              formControlName="yield_etf"
              min="0.5"
              max="30"
              step="0.5"
            />
          </div>
        </div>
        <p class="fi-caption text-ink-2 mt-1.5">
          Usada no preço justo de Bazin (dividendo anual ÷ meta). BDRs são avaliadas por Graham/DCF;
          ETFs usam só dividend yield (sem Graham/DCF, que exigem fundamentos de empresa).
        </p>
      </div>
      <div class="fi-block">
        <h2 class="fi-title m-0 mb-2 text-ink">Notificações e recomendação</h2>

        @if (!pushEnabled()) {
          <div class="p-3 rounded-md bg-attention/10 border border-attention/40 mb-4 flex gap-3">
            <lucide-icon name="smartphone" size="18" class="text-attention mt-0.5"></lucide-icon>
            <div class="fi-body">
              <div class="fi-label text-ink">As notificações requerem o app instalado</div>
              <div class="text-ink-2 mt-0.5">
                Nenhum aparelho registrado nesta conta. As preferências abaixo ficam salvas e passam
                a valer assim que você entrar pelo app — no navegador elas não disparam nada.
              </div>
            </div>
          </div>
        } @else {
          <div class="notice notice-brand mb-4">
            <lucide-icon name="smartphone" size="18" class="text-brand mt-0.5"></lucide-icon>
            <div class="fi-body text-ink-2">
              {{ registeredDevices() }}
              {{ registeredDevices() === 1 ? 'aparelho recebendo' : 'aparelhos recebendo' }}
              notificações desta conta.
            </div>
          </div>
        }

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label block mb-1.5">Alertas de preço</label>
            <label class="fi-body flex items-center gap-2 py-2 text-ink cursor-pointer">
              <input type="checkbox" formControlName="notify_price_alerts" class="accent-brand" />
              Notificar (imediato)
            </label>
          </div>

          <div>
            <label class="field-label block mb-1.5"> Resumo de oportunidades — cadência </label>
            <select formControlName="opportunities_frequency" class="input">
              @for (f of frequencyOptions; track f.key) {
                <option [value]="f.key">{{ f.label }}</option>
              }
            </select>
          </div>

          <div>
            <label class="field-label block mb-1.5">Perfil de risco</label>
            <select formControlName="risk_profile" class="input">
              @for (r of riskProfileOptions; track r.key) {
                <option [value]="r.key">{{ r.label }}</option>
              }
            </select>
            <p class="fi-caption text-ink-2 mt-1">
              Ajusta o peso de cada indicador no score de oportunidade.
            </p>
          </div>

          <div>
            <span class="fi-label block text-ink-2 mb-1.5" id="rotulo-densidade">
              Densidade da tela
            </span>
            <div class="flex items-center gap-2" role="group" aria-labelledby="rotulo-densidade">
              <button
                type="button"
                class="subtab-btn"
                [class.active]="densidade.density() === 'comfortable'"
                [attr.aria-pressed]="densidade.density() === 'comfortable'"
                (click)="densidade.set('comfortable')"
              >
                Confortável
              </button>
              <button
                type="button"
                class="subtab-btn"
                [class.active]="densidade.density() === 'compact'"
                [attr.aria-pressed]="densidade.density() === 'compact'"
                (click)="densidade.set('compact')"
              >
                Compacta
              </button>
            </div>
            <p class="fi-caption text-ink-2 mt-1">
              Vale em todas as telas e acompanha a sua conta, não este aparelho.
            </p>
          </div>
        </div>

        <div class="mt-4 pt-4 border-t border-hairline">
          <label class="field-label block mb-2">Categorias preferidas</label>
          <div class="flex flex-wrap gap-3">
            @for (cat of categories; track cat.key) {
              <label class="fi-body flex items-center gap-1.5 text-ink">
                <input
                  type="checkbox"
                  class="accent-brand"
                  [checked]="isPreferredCategory(cat.key)"
                  (change)="togglePreferredCategory(cat.key, $any($event.target).checked)"
                />
                {{ cat.label }}
              </label>
            }
          </div>
          <p class="fi-caption text-ink-2 mt-1.5">
            Ativos dessas categorias ganham um pequeno boost no score de oportunidade.
          </p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
          <div>
            <label class="field-label block mb-1.5">Setores preferidos</label>
            <input
              type="text"
              formControlName="preferred_sectors"
              placeholder="Ex.: Energia, Bancos, Varejo"
              class="input"
            />
          </div>
          <div>
            <label class="field-label block mb-1.5">Ativos excluídos</label>
            <input
              type="text"
              formControlName="excluded_tickers"
              placeholder="Ex.: MGLU3, IRBR3"
              class="input"
            />
          </div>
        </div>
      </div>
      <div class="flex items-center justify-end gap-3 mt-1">
        <span
          class="fi-body"
          [class.text-favorable]="message().startsWith('✓')"
          [class.text-adverse]="message().startsWith('✗')"
          *ngIf="message()"
          >{{ message() }}</span
        >
        <button
          type="button"
          class="btn-primary"
          (click)="savePreferencias()"
          [disabled]="saving()"
        >
          <lucide-icon [name]="saving() ? 'loader-circle' : 'check'" size="16"></lucide-icon>
          {{ saving() ? 'Salvando...' : 'Salvar' }}
        </button>
      </div>
    </form>
  `,
})
export class PreferencesComponent implements OnInit {
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
