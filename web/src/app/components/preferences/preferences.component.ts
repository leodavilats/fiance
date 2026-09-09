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
import { SectionComponent } from '../section/section.component';

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

const YIELDS: {
  control: 'yield_stock' | 'yield_fii' | 'yield_bdr' | 'yield_etf';
  label: string;
}[] = [
  { control: 'yield_stock', label: 'Ações BR' },
  { control: 'yield_fii', label: 'FIIs' },
  { control: 'yield_bdr', label: 'BDRs' },
  { control: 'yield_etf', label: 'ETFs' },
];

@Component({
  selector: 'app-preferences',
  standalone: true,
  imports: [PageHeaderComponent, ReactiveFormsModule, LucideAngularModule, SectionComponent],
  template: `
    <app-page-header
      title="Preferências"
      question="Com que régua o fiance avalia o que é seu?"
      scope="Vale para todas as telas e acompanha a sua conta, não este aparelho."
    />

    <form [formGroup]="form">
      <app-section
        title="Preço justo"
        tone="title"
        hint="O dividend yield que você exige de cada classe. É o divisor do preço-teto de Bazin: dividendo anual ÷ meta. Exigir mais derruba o preço justo, e menos ativos passam."
      >
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-3 max-w-reading">
          @for (y of yields; track y.control) {
            <div class="field">
              <label class="field-label" [attr.for]="y.control">{{ y.label }} (%)</label>
              <input
                type="number"
                [id]="y.control"
                class="input"
                [formControlName]="y.control"
                min="0.5"
                max="30"
                step="0.5"
              />
            </div>
          }
        </div>
        <p class="fi-caption text-ink-3 m-0 mt-2 max-w-reading">
          BDRs também passam por Graham e DCF. ETFs não: os dois exigem fundamento de empresa, e um
          ETF não tem um.
        </p>
      </app-section>

      <app-section
        title="Score de oportunidade"
        tone="title"
        hint="O que faz um ativo subir na lista de Descobrir. Nada aqui altera o preço justo — muda a ordem, não o veredito."
      >
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-3">
          <div class="field">
            <label class="field-label" for="perfil-de-risco">Perfil de risco</label>
            <select id="perfil-de-risco" formControlName="risk_profile" class="input">
              @for (r of riskProfileOptions; track r.key) {
                <option [value]="r.key">{{ r.label }}</option>
              }
            </select>
            <p class="fi-caption text-ink-3 m-0 mt-1">Ajusta o peso de cada indicador no score.</p>
          </div>

          <div class="field">
            <label class="field-label" for="setores-preferidos">Setores preferidos</label>
            <input
              type="text"
              id="setores-preferidos"
              formControlName="preferred_sectors"
              placeholder="Energia, Bancos, Varejo"
              class="input"
            />
          </div>

          <div class="field">
            <label class="field-label" for="ativos-excluidos">Ativos que nunca quero ver</label>
            <input
              type="text"
              id="ativos-excluidos"
              formControlName="excluded_tickers"
              placeholder="MGLU3, IRBR3"
              class="input"
            />
            <p class="fi-caption text-ink-3 m-0 mt-1">
              Saem de Descobrir. Posição sua continua aparecendo no Patrimônio.
            </p>
          </div>

          <fieldset class="field m-0 p-0 border-0">
            <legend class="field-label p-0">Categorias preferidas</legend>
            <div class="flex flex-wrap gap-x-4 gap-y-2 mt-1">
              @for (cat of categories; track cat.key) {
                <label class="fi-body flex items-center gap-1.5 text-ink cursor-pointer">
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
          </fieldset>
        </div>
      </app-section>

      <app-section title="Avisos" tone="title">
        @if (pushEnabled()) {
          <div class="notice notice-brand mt-3">
            <lucide-icon name="smartphone" size="18" aria-hidden="true"></lucide-icon>
            <p class="fi-body text-ink-2 m-0">
              {{ registeredDevices() }}
              {{ registeredDevices() === 1 ? 'aparelho recebe' : 'aparelhos recebem' }}
              os avisos desta conta.
            </p>
          </div>
        } @else {
          <div class="notice notice-attention mt-3">
            <lucide-icon name="smartphone" size="18" aria-hidden="true"></lucide-icon>
            <div>
              <p class="fi-label text-ink m-0">Aviso exige o app instalado</p>
              <p class="fi-body text-ink-2 m-0 mt-1">
                Nenhum aparelho registrado nesta conta. O que você escolher aqui fica salvo e passa
                a valer quando você entrar pelo app; no navegador nada dispara.
              </p>
            </div>
          </div>
        }

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-4">
          <fieldset class="field m-0 p-0 border-0">
            <legend class="field-label p-0">Alerta de preço</legend>
            <label class="fi-body flex items-center gap-2 py-2 text-ink cursor-pointer">
              <input type="checkbox" formControlName="notify_price_alerts" class="accent-brand" />
              Avisar assim que o preço bater
            </label>
          </fieldset>

          <div class="field">
            <label class="field-label" for="cadencia">Resumo de oportunidades</label>
            <select id="cadencia" formControlName="opportunities_frequency" class="input">
              @for (f of frequencyOptions; track f.key) {
                <option [value]="f.key">{{ f.label }}</option>
              }
            </select>
          </div>
        </div>
      </app-section>

      <div class="fi-block flex items-center justify-end gap-4 flex-wrap">
        @if (resultado() === 'ok') {
          <p class="fi-body text-favorable m-0" role="status">Preferências salvas</p>
        } @else if (resultado() === 'erro') {
          <p class="fi-body text-adverse m-0" role="alert">
            Não conseguimos salvar. Suas preferências anteriores continuam valendo.
          </p>
        }
        <button
          type="button"
          class="btn-primary"
          (click)="savePreferencias()"
          [disabled]="saving()"
        >
          <lucide-icon [name]="saving() ? 'loader-circle' : 'check'" size="16"></lucide-icon>
          {{ saving() ? 'Salvando…' : 'Salvar' }}
        </button>
      </div>

      <app-section
        title="Esta tela"
        tone="title"
        hint="Muda na hora, sem passar pelo Salvar acima."
      >
        <span class="fi-label block text-ink-2 mt-3 mb-1.5" id="rotulo-densidade"> Densidade </span>
        <div class="segmented" role="group" aria-labelledby="rotulo-densidade">
          <button
            type="button"
            class="segmented-option"
            [attr.aria-pressed]="densidade.density() === 'comfortable'"
            (click)="densidade.set('comfortable')"
          >
            Confortável
          </button>
          <button
            type="button"
            class="segmented-option"
            [attr.aria-pressed]="densidade.density() === 'compact'"
            (click)="densidade.set('compact')"
          >
            Compacta
          </button>
        </div>
        <p class="fi-caption text-ink-3 m-0 mt-2 max-w-reading">
          Compacta encurta a altura de linha das tabelas e o espaço entre seções. Nenhum número
          muda.
        </p>
      </app-section>
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
  readonly yields = YIELDS;

  readonly saving = signal(false);
  readonly resultado = signal<'ok' | 'erro' | null>(null);

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
    this.resultado.set(null);

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
          this.resultado.set('ok');
          setTimeout(() => this.resultado.set(null), 3000);
        },
        error: () => {
          this.saving.set(false);
          this.resultado.set('erro');
          setTimeout(() => this.resultado.set(null), 6000);
        },
      });
  }
}
