import { CommonModule } from '@angular/common';
import { Component, computed, inject, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { EntitlementService } from '../../core';

@Component({
  selector: 'app-gate',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    @if (visible()) {
      <section
        class="card"
        role="region"
        [attr.aria-label]="'Recurso do plano Premium: ' + title()"
      >
        <h3 class="fi-metric-sm flex items-center gap-2 m-0 mb-1 text-ink">
          <lucide-icon name="lock" size="16" aria-hidden="true"></lucide-icon>
          {{ title() }}
        </h3>

        @if (preview()) {
          <p class="fi-body text-ink m-0 mb-2">{{ preview() }}</p>
        }

        <p class="fi-body text-ink-2 m-0 max-w-prose">{{ reason() }}</p>

        @if (limitReached()) {
          <p class="fi-caption text-ink-3 m-0 mt-2">
            O teto reinicia no começo do mês. Ativos da sua carteira nunca contam.
          </p>
        }

        <div class="flex flex-wrap items-center gap-3 mt-4">
          <a class="btn-primary" routerLink="/voce/plano" (click)="upgrade.emit()">
            Ver o plano Premium
          </a>
          @if (secondaryLabel()) {
            <span class="fi-body text-ink-3">{{ secondaryLabel() }}</span>
          }
        </div>
      </section>
    }
  `,
})
export class GateComponent {
  private readonly entitlements = inject(EntitlementService);

  readonly feature = input.required<string>();
  readonly title = input('Disponível no Premium');

  readonly preview = input<string>('');
  readonly reason = input('Este recurso faz parte do plano Premium.');
  readonly limitReached = input(false);
  readonly secondaryLabel = input<string>('');

  readonly upgrade = output<void>();

  readonly visible = computed(
    () => !this.entitlements.unrestricted() && !this.entitlements.allows(this.feature())
  );
}
