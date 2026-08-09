import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, output, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { PriceAlertTriggered, RecommendService } from '../../core';

const SESSION_KEY = 'fianceai_alerts_dismissed';

@Component({
  selector: 'app-alert-modal',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    @if (visible()) {
      <div
        class="fixed inset-0 z-[300] bg-black/60 flex items-center justify-center p-4"
        (click)="dismiss()"
      >
        <div
          class="relative w-full max-w-md rounded-xl border border-border shadow-2xl"
          style="background: var(--panel)"
          (click)="$event.stopPropagation()"
        >
          <div class="flex items-center justify-between px-5 pt-5 pb-3 border-b border-border">
            <h2 class="flex items-center gap-2 text-base font-bold m-0 text-tx">
              <lucide-icon name="bell-ring" size="18" class="text-warn"></lucide-icon>
              Alertas de Preço Atingidos
            </h2>
            <button
              type="button"
              class="w-8 h-8 grid place-items-center rounded-lg text-muted hover:text-tx hover:bg-panel-2 transition-colors cursor-pointer border-0 bg-transparent"
              (click)="dismiss()"
            >
              <lucide-icon name="x" size="16"></lucide-icon>
            </button>
          </div>
          <div class="flex flex-col gap-2 p-5 max-h-80 overflow-y-auto">
            @for (a of triggered(); track a.id) {
              <div
                class="flex items-center justify-between gap-3 p-3 rounded-lg border border-warn bg-warn/5"
              >
                <div class="flex flex-col gap-0.5">
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-tx">{{ a.ticker }}</span>
                    <span class="text-xs text-muted">
                      {{ a.condition === 'below' ? 'abaixo de' : 'acima de' }}
                      R$ {{ a.target_price | number: '1.2-2' }}
                    </span>
                  </div>
                  <div class="text-sm">
                    Preço atual:
                    <span
                      class="font-semibold"
                      [class.text-accent]="a.condition === 'above'"
                      [class.text-warn]="a.condition === 'below'"
                    >
                      R$ {{ a.current_price | number: '1.2-2' }}
                    </span>
                  </div>
                  @if (a.note) {
                    <div class="text-xs text-muted">{{ a.note }}</div>
                  }
                </div>
                <lucide-icon
                  name="triangle-alert"
                  size="20"
                  class="text-warn shrink-0"
                ></lucide-icon>
              </div>
            }
          </div>
          <div class="flex items-center justify-between gap-3 px-5 pb-5">
            <a
              routerLink="/config"
              class="text-xs text-accent hover:underline no-underline"
              (click)="dismiss()"
            >
              Gerenciar alertas
            </a>
            <button
              type="button"
              class="px-4 py-2 rounded-lg text-sm font-medium cursor-pointer bg-accent text-white border-0 hover:opacity-90 transition-opacity"
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

  visible = signal(false);
  triggered = signal<PriceAlertTriggered[]>([]);

  ngOnInit(): void {
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
