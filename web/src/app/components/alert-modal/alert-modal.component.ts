import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, output, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService, PriceAlertTriggered, RecommendService } from '../../core';

const SESSION_KEY = 'fiance_alerts_dismissed';

@Component({
  selector: 'app-alert-modal',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    @if (visible()) {
      <div
        class="fixed inset-0 z-[300] fi-overlay flex items-center justify-center p-4"
        (click)="dismiss()"
      >
        <div
          class="relative w-full max-w-md rounded-xl border border-hairline shadow-popover"
          style="background: var(--fi-ground-1)"
          (click)="$event.stopPropagation()"
        >
          <div class="flex items-center justify-between px-5 pt-5 pb-3 border-b border-hairline">
            <h2 class="flex items-center gap-2 text-base font-bold m-0 text-ink">
              <lucide-icon name="bell-ring" size="18" class="text-attention"></lucide-icon>
              Alertas de Preço Atingidos
            </h2>
            <button
              type="button"
              class="w-8 h-8 grid place-items-center rounded-lg text-ink-2 hover:text-ink hover:bg-ground-2 transition-colors cursor-pointer border-0 bg-transparent"
              (click)="dismiss()"
            >
              <lucide-icon name="x" size="16"></lucide-icon>
            </button>
          </div>
          <div class="flex flex-col gap-2 p-5 max-h-80 overflow-y-auto">
            @for (a of triggered(); track a.id) {
              <div
                class="flex items-center justify-between gap-3 p-3 rounded-lg border border-attention bg-attention/5"
              >
                <div class="flex flex-col gap-0.5">
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-ink">{{ a.ticker }}</span>
                    <span class="text-xs text-ink-2">
                      {{ a.condition === 'below' ? 'abaixo de' : 'acima de' }}
                      R$ {{ a.target_price | number: '1.2-2' }}
                    </span>
                  </div>
                  <div class="text-sm">
                    Preço atual:
                    <span
                      class="font-semibold"
                      [class.text-brand]="a.condition === 'above'"
                      [class.text-attention]="a.condition === 'below'"
                    >
                      R$ {{ a.current_price | number: '1.2-2' }}
                    </span>
                  </div>
                  @if (a.note) {
                    <div class="text-xs text-ink-2">{{ a.note }}</div>
                  }
                </div>
                <lucide-icon
                  name="triangle-alert"
                  size="20"
                  class="text-attention shrink-0"
                ></lucide-icon>
              </div>
            }
          </div>
          <div class="flex items-center justify-between gap-3 px-5 pb-5">
            <a
              routerLink="/config"
              class="text-xs text-brand hover:underline no-underline"
              (click)="dismiss()"
            >
              Gerenciar alertas
            </a>
            <button
              type="button"
              class="px-4 py-2 rounded-lg text-sm font-medium cursor-pointer bg-brand text-on-brand border-0 hover:opacity-90 transition-opacity"
              (click)="dismiss()"
            >
              Entendido
            </button>
          </div>
        </div>
      </div>
    }
  `,
})
export class AlertModalComponent implements OnInit {
  private svc = inject(RecommendService);
  private auth = inject(AuthService);

  visible = signal(false);
  triggered = signal<PriceAlertTriggered[]>([]);

  ngOnInit(): void {
    if (!this.auth.isAuthenticated()) return;
    if (sessionStorage.getItem(SESSION_KEY)) return;

    this.svc.checkAlerts().subscribe({
      next: list => {
        if (list.length > 0) {
          this.triggered.set(list);
          this.visible.set(true);
        }
      },
      error: () => {},
    });
  }

  dismiss(): void {
    this.visible.set(false);
    sessionStorage.setItem(SESSION_KEY, '1');
  }
}
