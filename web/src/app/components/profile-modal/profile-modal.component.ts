import { CommonModule } from '@angular/common';
import { Component, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AppUser } from '../../core';

@Component({
  selector: 'app-profile-modal',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    @if (open()) {
      <div
        class="fixed inset-0 z-[300] fi-overlay flex items-center justify-center p-4"
        (click)="close.emit()"
      >
        <div
          class="relative w-full max-w-sm rounded-xl border border-hairline shadow-popover"
          style="background: var(--fi-ground-1)"
          (click)="$event.stopPropagation()"
        >
          <div class="flex items-center justify-between px-5 pt-5 pb-3 border-b border-hairline">
            <h2 class="text-base font-bold m-0 text-ink">Sua conta</h2>
            <button
              type="button"
              class="w-8 h-8 grid place-items-center rounded-lg text-ink-2 hover:text-ink hover:bg-ground-2 transition-colors cursor-pointer border-0 bg-transparent"
              (click)="close.emit()"
              aria-label="Fechar"
            >
              <lucide-icon name="x" size="16"></lucide-icon>
            </button>
          </div>
          <div class="flex flex-col items-center gap-3 p-6">
            @if (user()) {
              <img
                [src]="user()!.picture"
                [alt]="user()!.name"
                referrerpolicy="no-referrer"
                class="w-20 h-20 rounded-full border border-hairline"
              />
              <div class="text-center">
                <div class="text-lg font-bold text-ink">{{ user()!.name }}</div>
                <div class="text-sm text-ink-2">{{ user()!.email }}</div>
              </div>
            }
          </div>
          <nav class="px-5 pb-4" aria-label="Sua área">
            <ul class="list-none m-0 p-0 flex flex-col">
              @for (item of shortcuts; track item.path) {
                <li>
                  <a
                    [routerLink]="item.path"
                    (click)="close.emit()"
                    class="flex items-center gap-3 px-3 py-2.5 rounded-md no-underline text-ink hover:bg-ground-2 transition-colors"
                  >
                    <lucide-icon
                      [name]="item.icon"
                      size="16"
                      class="text-ink-3"
                      aria-hidden="true"
                    ></lucide-icon>
                    <span class="flex-1 min-w-0">
                      <span class="fi-body block">{{ item.label }}</span>
                      <span class="fi-caption text-ink-3 block">{{ item.hint }}</span>
                    </span>
                    <lucide-icon
                      name="chevron-right"
                      size="14"
                      class="text-ink-3 shrink-0"
                      aria-hidden="true"
                    ></lucide-icon>
                  </a>
                </li>
              }
            </ul>
          </nav>

          <div class="px-5 pb-5 pt-1 border-t border-hairline mt-1">
            <button
              type="button"
              class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm cursor-pointer bg-ground-2 border border-hairline text-adverse hover:bg-adverse hover:text-on-brand transition-colors"
              (click)="logout.emit()"
            >
              <lucide-icon name="log-out" size="16"></lucide-icon> Sair da conta
            </button>
          </div>
        </div>
      </div>
    }
  `,
})
export class ProfileModalComponent {
  readonly open = input(false);
  readonly user = input<AppUser | null>(null);
  readonly close = output<void>();

  readonly shortcuts = [
    {
      path: '/voce/preferencias',
      label: 'Preferências',
      hint: 'Perfil de risco, categorias e exclusões',
      icon: 'sliders-horizontal',
    },
    { path: '/voce/alertas', label: 'Alertas', hint: 'Preço-alvo e avisos', icon: 'bell' },
    {
      path: '/voce/conta',
      label: 'Conta e dados',
      hint: 'Proveniência das cotações e cache',
      icon: 'shield-check',
    },
  ] as const;
  readonly logout = output<void>();
}
