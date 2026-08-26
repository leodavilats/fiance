import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
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
import {
  ActivityService,
  AuthService,
  GlobalSearchService,
  LoadingService,
  ThemeService,
} from './core';
import {
  ActivityDrawerComponent,
  AlertModalComponent,
  GlobalLoaderComponent,
  GlobalSearchComponent,
  LogoComponent,
  ProfileModalComponent,
  SnackbarComponent,
} from './components';

interface NavDestination {
  readonly path: string;
  readonly label: string;
  readonly icon: string;
}

const DESTINATIONS: readonly NavDestination[] = [
  { path: '/hoje', label: 'Hoje', icon: 'sunrise' },
  { path: '/carteira', label: 'Carteira', icon: 'wallet' },
  { path: '/descobrir', label: 'Descobrir', icon: 'compass' },
  { path: '/estrategia', label: 'Estratégia', icon: 'target' },
];

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    LucideAngularModule,
    ActivityDrawerComponent,
    GlobalLoaderComponent,
    GlobalSearchComponent,
    SnackbarComponent,
    AlertModalComponent,
    LogoComponent,
    ProfileModalComponent,
  ],
  template: `
    <app-global-loader />
    <app-snackbar />
    <app-alert-modal />
    <app-global-search />
    <app-activity-drawer />
    <app-profile-modal
      [open]="showProfile()"
      [user]="auth.user()"
      (close)="showProfile.set(false)"
      (logout)="logout()"
    />

    @if (auth.user(); as user) {
      <header class="border-b border-hairline">
        <div
          class="max-w-dense mx-auto px-3 sm:px-5 flex items-center justify-between gap-4 h-14 sm:h-16"
        >
          <a routerLink="/hoje" class="flex items-center gap-2.5 no-underline" title="fiance">
            <app-logo [size]="30" />
            <span class="text-lg font-bold text-ink tracking-tight">fiance</span>
          </a>

          <nav class="hidden md:block" aria-label="Navegação principal">
            <ul class="flex items-center gap-1 list-none m-0 p-0">
              @for (d of destinations; track d.path) {
                <li>
                  <a [routerLink]="d.path" routerLinkActive="nav-active" class="nav-link">
                    <lucide-icon [name]="d.icon" size="16"></lucide-icon>
                    {{ d.label }}
                  </a>
                </li>
              }
            </ul>
          </nav>

          <div class="flex items-center gap-2">
            <button
              class="hidden sm:flex items-center gap-2 h-9 px-2.5 rounded-md cursor-pointer bg-transparent border border-hairline text-ink-2 hover:text-ink hover:bg-ground-2 transition-colors"
              type="button"
              (click)="search.show()"
              aria-label="Buscar tela ou ativo"
            >
              <lucide-icon name="search" size="16"></lucide-icon>
              <kbd class="fi-caption border border-hairline rounded-sm px-1">{{ searchHint }}</kbd>
            </button>
            <button
              class="w-9 h-9 grid place-items-center rounded-md cursor-pointer bg-transparent border border-hairline text-ink hover:bg-ground-2 transition-colors"
              type="button"
              (click)="activity.show()"
              title="Atividade recente"
              aria-label="Abrir atividade recente"
            >
              <lucide-icon name="history" size="18"></lucide-icon>
            </button>
            <button
              class="w-9 h-9 grid place-items-center rounded-md cursor-pointer bg-transparent border border-hairline text-ink hover:bg-ground-2 transition-colors"
              type="button"
              (click)="theme.toggle()"
              [title]="theme.theme() === 'dark' ? 'Modo claro' : 'Modo escuro'"
              [attr.aria-label]="
                theme.theme() === 'dark' ? 'Mudar para modo claro' : 'Mudar para modo escuro'
              "
            >
              <lucide-icon
                [name]="theme.theme() === 'dark' ? 'sun' : 'moon'"
                size="18"
              ></lucide-icon>
            </button>
            <button
              type="button"
              class="cursor-pointer border-0 bg-transparent p-0 rounded-full"
              (click)="showProfile.set(true)"
              title="Sua conta"
              aria-label="Abrir sua conta"
            >
              <img
                [src]="user.picture"
                [alt]="user.name"
                class="w-9 h-9 rounded-full border border-hairline hover:opacity-80 transition-opacity"
                referrerpolicy="no-referrer"
              />
            </button>
          </div>
        </div>
      </header>
    }

    <main class="max-w-dense mx-auto px-3 sm:px-5 pt-5 sm:pt-6 pb-24 md:pb-10">
      <router-outlet />
    </main>

    @if (auth.user()) {
      <nav
        class="md:hidden fixed bottom-0 left-0 right-0 border-t border-hairline bg-ground-1"
        style="padding-bottom: env(safe-area-inset-bottom); z-index: var(--fi-z-nav);"
        aria-label="Navegação principal"
      >
        <ul class="flex items-stretch justify-around h-14 list-none m-0 p-0">
          @for (d of destinations; track d.path) {
            <li class="flex-1 flex">
              <a
                [routerLink]="d.path"
                routerLinkActive="nav-active-mob"
                class="flex flex-col items-center justify-center gap-0.5 px-1 flex-1 text-ink-2 no-underline text-xs font-medium transition-colors"
              >
                <lucide-icon [name]="d.icon" size="20"></lucide-icon>
                <span>{{ d.label }}</span>
              </a>
            </li>
          }
          <li class="flex-1 flex">
            <a
              routerLink="/voce"
              routerLinkActive="nav-active-mob"
              class="flex flex-col items-center justify-center gap-0.5 px-1 flex-1 text-ink-2 no-underline text-xs font-medium transition-colors"
            >
              <lucide-icon name="sliders-horizontal" size="20"></lucide-icon>
              <span>Você</span>
            </a>
          </li>
        </ul>
      </nav>
    }
  `,
  styles: [
    `
      .nav-link {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.5rem 0.75rem;
        border-radius: var(--fi-radius-md);
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--fi-ink-2);
        text-decoration: none;
        transition: color var(--fi-motion-fast) ease;
      }
      .nav-link:hover {
        color: var(--fi-ink-1);
      }
      :host ::ng-deep a.nav-active {
        color: var(--fi-ink-1);
        font-weight: 600;
        box-shadow: inset 0 -2px 0 var(--fi-brand);
      }
      :host ::ng-deep a.nav-active-mob {
        color: var(--fi-brand);
      }
      :host ::ng-deep a:focus-visible,
      :host ::ng-deep button:focus-visible {
        outline: var(--fi-focus-ring) solid var(--fi-brand);
        outline-offset: var(--fi-focus-offset);
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
  readonly search = inject(GlobalSearchService);
  readonly activity = inject(ActivityService);

  /** O atalho muda de tecla por plataforma; o rótulo tem que acompanhar. */
  readonly searchHint = /Mac|iPhone|iPad/.test(navigator.platform) ? '⌘K' : 'Ctrl K';
  readonly showProfile = signal(false);
  readonly destinations = DESTINATIONS;

  private readonly router = inject(Router);
  private readonly loading = inject(LoadingService);

  logout(): void {
    this.showProfile.set(false);
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
