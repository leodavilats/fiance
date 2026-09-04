import { CommonModule } from '@angular/common';
import { Component, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    <!-- veredito: o título de um estado vazio diz o que o sistema concluiu sobre a situação -->
    <div class="py-8 px-1 max-w-reading">
      <h3 class="fi-verdict-sm text-ink m-0 mb-1 flex items-center gap-2">
        @if (icon()) {
          <lucide-icon
            [name]="icon()"
            size="16"
            class="text-ink-3"
            aria-hidden="true"
          ></lucide-icon>
        }
        {{ title() }}
      </h3>

      <p class="fi-body text-ink-2 m-0 mb-1">{{ reason() }}</p>

      @if (nextStep()) {
        <p class="fi-caption text-ink-3 m-0 mb-4">{{ nextStep() }}</p>
      } @else {
        <div class="mb-4"></div>
      }

      @if (actionLabel()) {
        <div class="flex flex-wrap items-center gap-3">
          @if (actionRoute()) {
            <a [routerLink]="actionRoute()" class="btn-primary no-underline">{{ actionLabel() }}</a>
          } @else {
            <button type="button" class="btn-primary" (click)="action.emit()">
              {{ actionLabel() }}
            </button>
          }
          @if (secondaryLabel() && secondaryRoute()) {
            <a [routerLink]="secondaryRoute()" class="fi-caption text-brand no-underline">
              {{ secondaryLabel() }} →
            </a>
          }
        </div>
      }
    </div>
  `,
})
export class EmptyStateComponent {
  readonly title = input.required<string>();
  readonly reason = input.required<string>();
  readonly nextStep = input<string>('');

  readonly actionLabel = input<string>('');
  readonly actionRoute = input<string | null>(null);
  readonly secondaryLabel = input<string>('');
  readonly secondaryRoute = input<string | null>(null);
  readonly icon = input<string>('');

  readonly action = output<void>();
}
