import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import {
  NavigationCancel,
  NavigationEnd,
  NavigationError,
  NavigationStart,
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService, LoadingService, ThemeService } from './core';
import { AlertModalComponent, GlobalLoaderComponent, SnackbarComponent } from './components';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    LucideAngularModule,
    GlobalLoaderComponent,
    SnackbarComponent,
    AlertModalComponent,
  ],
  template: `
    <app-global-loader />
    <app-snackbar />
    <app-alert-modal />
    <div class="max-w-[1180px] mx-auto px-3 sm:px-5 pt-4 sm:pt-6 pb-20 sm:pb-10">
      @if (auth.user(); as user) {
        <header class="flex justify-between items-center gap-4 py-2 px-1 pb-[14px] sm:pb-[18px]">
          <div style="display:flex; align-items:center; gap:10px;">
            <div
              class="w-9 h-9 sm:w-11 sm:h-11 grid place-items-center rounded-xl font-extrabold text-[1.2rem] sm:text-[1.4rem] text-[#0b0e14] bg-gradient-to-br from-accent to-accent-2"
            >
              f
            </div>
            <div>
              <h1 class="text-[1.3rem] sm:text-[1.7rem] font-bold m-0 text-tx">fianceAI</h1>
              <p class="m-0 text-xs sm:text-sm text-muted hidden sm:block">
                Sistema de gestão de ativos — descubra o que comprar, manter ou vender.
              </p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              class="w-9 h-9 grid place-items-center rounded-lg cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel hover:opacity-90 transition-opacity"
              type="button"
              (click)="theme.toggle()"
              [title]="theme.theme() === 'dark' ? 'Modo claro' : 'Modo escuro'"
            >
              <lucide-icon [name]="theme.theme() === 'dark' ? 'sun' : 'moon'" size="18"></lucide-icon>
            </button>
            <img
              [src]="user.picture"
              [title]="user.name"
              class="w-9 h-9 rounded-full border border-border"
              referrerpolicy="no-referrer"
            />
            <button
              class="w-9 h-9 grid place-items-center rounded-lg cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel hover:opacity-90 transition-opacity"
              type="button"
              (click)="logout()"
              title="Sair"
            >
              <lucide-icon name="x" size="18"></lucide-icon>
            </button>
          </div>
        </header>

        <nav class="hidden sm:flex flex-wrap gap-2 mb-6">
        <a
          routerLink="/dashboard"
          routerLinkActive="active"
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all no-underline"
        >
          <lucide-icon name="layout-dashboard" size="16"></lucide-icon> Dashboard
        </a>
        <a
          routerLink="/assets"
          routerLinkActive="active"
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all no-underline"
        >
          <lucide-icon name="briefcase" size="16"></lucide-icon> Meus Ativos
        </a>
        <a
          routerLink="/market"
          routerLinkActive="active"
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all no-underline"
        >
          <lucide-icon name="target" size="16"></lucide-icon> Mercado
        </a>
        <a
          routerLink="/config"
          routerLinkActive="active"
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all no-underline"
        >
          <lucide-icon name="settings" size="16"></lucide-icon> Configurações
        </a>
        </nav>
      }

      <router-outlet />
    </div>

    @if (auth.user()) {
      <nav
        class="mobile-bottom-nav fixed bottom-0 left-0 right-0 z-50 border-t border-border"
        style="background: var(--panel); padding-bottom: env(safe-area-inset-bottom);"
      >
      <div class="flex items-stretch justify-around h-14">
        <a
          routerLink="/dashboard"
          routerLinkActive="active-mob"
          class="flex flex-col items-center justify-center gap-0.5 px-2 flex-1 text-muted no-underline text-[10px] font-medium transition-colors"
        >
          <lucide-icon name="layout-dashboard" size="20"></lucide-icon>
          <span>Início</span>
        </a>
        <a
          routerLink="/assets"
          routerLinkActive="active-mob"
          class="flex flex-col items-center justify-center gap-0.5 px-2 flex-1 text-muted no-underline text-[10px] font-medium transition-colors"
        >
          <lucide-icon name="briefcase" size="20"></lucide-icon>
          <span>Ativos</span>
        </a>
        <a
          routerLink="/market"
          routerLinkActive="active-mob"
          class="flex flex-col items-center justify-center gap-0.5 px-2 flex-1 text-muted no-underline text-[10px] font-medium transition-colors"
        >
          <lucide-icon name="target" size="20"></lucide-icon>
          <span>Mercado</span>
        </a>
        <a
          routerLink="/config"
          routerLinkActive="active-mob"
          class="flex flex-col items-center justify-center gap-0.5 px-2 flex-1 text-muted no-underline text-[10px] font-medium transition-colors"
        >
          <lucide-icon name="settings" size="20"></lucide-icon>
          <span>Config</span>
        </a>
      </div>
      </nav>
    }
  `,
  styles: [
    `
      :host ::ng-deep a.active {
        background: linear-gradient(135deg, #4ade80, #22d3ee);
        color: #0b0e14;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(34, 211, 238, 0.3);
      }
      :host ::ng-deep a.active-mob {
        color: var(--accent);
      }
      a {
        text-decoration: none !important;
      }
    `,
  ],
})
export class AppComponent {
  readonly theme = inject(ThemeService);
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly loading = inject(LoadingService);

  logout(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }

  private _navShown = false;
  private _navTimer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    this.router.events.subscribe(e => {
      if (e instanceof NavigationStart) {
        if (this._navShown || this._navTimer) return;
        this._navTimer = setTimeout(() => {
          this._navTimer = null;
          this._navShown = true;
          this.loading.show();
        }, 150);
      } else if (
        e instanceof NavigationEnd ||
        e instanceof NavigationCancel ||
        e instanceof NavigationError
      ) {
        if (this._navTimer) {
          clearTimeout(this._navTimer);
          this._navTimer = null;
        }
        if (this._navShown) {
          this._navShown = false;
          this.loading.hide();
        }
      }
    });
  }
}
