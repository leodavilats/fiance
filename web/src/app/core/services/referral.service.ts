import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { environment } from '../../../environments/environment';

export interface ReferralStatus {
  code: string;
  reward_days: number;
  max_credited_days: number;
  attributed: number;
  qualified: number;
  pending: number;
  days_earned: number;
  credited_until: number | null;
  credited_days_total: number;
}

/**
 * Indicação.
 *
 * O serviço não guarda quem foi indicado porque o servidor não devolve isso:
 * quem clicou no link de alguém não escolheu aparecer numa tela dessa pessoa.
 * As contagens bastam para o programa funcionar.
 */
@Injectable({ providedIn: 'root' })
export class ReferralService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBaseUrl;

  private readonly state = signal<ReferralStatus | null>(null);
  readonly status = this.state.asReadonly();

  load(): void {
    this.http.get<ReferralStatus>(`${this.base}/referral`).subscribe({
      next: res => this.state.set(res),
      error: () => this.state.set(null),
    });
  }

  rotate(): void {
    this.http.post<{ code: string }>(`${this.base}/referral/rotate`, {}).subscribe({
      next: () => this.load(),
    });
  }
}
