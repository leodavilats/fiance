import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { environment } from '../../../environments/environment';

export interface EntitlementDecision {
  allowed: boolean;
  feature: string;
  plan: string;
  required_plan: string;
  reason: string;
  limit: number | null;
  used: number;
  limit_reached: boolean;
}

export interface Entitlements {
  plan: string;

  unrestricted: boolean;
  in_trial: boolean;
  trial_ends_at: number | null;
  trial_days_left: number | null;
  features: Record<string, boolean>;
  limits: Record<string, number | null>;
}

@Injectable({ providedIn: 'root' })
export class EntitlementService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBaseUrl;

  private readonly state = signal<Entitlements | null>(null);
  private loaded = false;

  readonly entitlements = this.state.asReadonly();

  readonly unrestricted = computed(() => this.state()?.unrestricted ?? true);
  readonly plan = computed(() => this.state()?.plan ?? 'premium');
  readonly inTrial = computed(() => this.state()?.in_trial ?? false);
  readonly trialDaysLeft = computed(() => this.state()?.trial_days_left ?? null);

  readonly trialEndingSoon = computed(() => {
    const dias = this.trialDaysLeft();
    return dias !== null && dias <= 3;
  });

  ensureLoaded(): void {
    if (this.loaded) return;
    this.loaded = true;

    this.http.get<Entitlements>(`${this.base}/entitlements`).subscribe({
      next: res => this.state.set(res),
      error: () => this.state.set(null),
    });
  }

  allows(feature: string): boolean {
    const atual = this.state();
    if (!atual || atual.unrestricted) return true;
    return atual.features[feature] ?? true;
  }

  limitFor(feature: string): number | null {
    return this.state()?.limits[feature] ?? null;
  }

  refresh(): void {
    this.loaded = false;
    this.ensureLoaded();
  }
}
