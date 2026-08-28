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
  /** `true` quando a régua está desligada — nenhum gate deve aparecer. */
  unrestricted: boolean;
  in_trial: boolean;
  trial_ends_at: number | null;
  trial_days_left: number | null;
  features: Record<string, boolean>;
  limits: Record<string, number | null>;
}

/**
 * Os direitos, consultados — nunca decididos aqui.
 *
 * O cliente usa isto para **não desenhar botão que não faz nada** e para
 * escolher entre a tela cheia e a prévia. A checagem que vale é a do servidor:
 * cliente adulterado não pode virar assinante, então nada aqui libera nada.
 */
@Injectable({ providedIn: 'root' })
export class EntitlementService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBaseUrl;

  private readonly state = signal<Entitlements | null>(null);
  private loaded = false;

  readonly entitlements = this.state.asReadonly();

  /**
   * Enquanto a resposta não chega, o produto se comporta como se tudo fosse
   * permitido.
   *
   * É o padrão certo: mostrar gate por um instante e depois removê-lo faria a
   * tela piscar um paywall para quem já paga — e piscar cobrança em quem
   * pagou é pior que demorar a mostrá-la para quem não pagou. O servidor
   * bloqueia de qualquer forma.
   */
  readonly unrestricted = computed(() => this.state()?.unrestricted ?? true);
  readonly plan = computed(() => this.state()?.plan ?? 'premium');
  readonly inTrial = computed(() => this.state()?.in_trial ?? false);
  readonly trialDaysLeft = computed(() => this.state()?.trial_days_left ?? null);

  /** Avisa nos últimos dias, não durante as duas semanas inteiras. */
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

  /** `true` quando a feature está liberada — ou quando a régua está desligada. */
  allows(feature: string): boolean {
    const atual = this.state();
    if (!atual || atual.unrestricted) return true;
    return atual.features[feature] ?? true;
  }

  limitFor(feature: string): number | null {
    return this.state()?.limits[feature] ?? null;
  }

  /** Reconsulta depois de uma compra ou de um cancelamento. */
  refresh(): void {
    this.loaded = false;
    this.ensureLoaded();
  }
}
