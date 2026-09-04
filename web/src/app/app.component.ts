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
  DensityService,
  EntitlementService,
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
  { path: '/voce', label: 'Você', icon: 'sliders-horizontal' },
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
    <!--
      Navegação em SPA é silenciosa para leitor de tela: a pessoa troca de tela
      e nada é anunciado, porque não houve carregamento de documento. Esta
      região diz o destino em voz alta, em modo polite para não cortar o que
      estiver sendo lido.
    -->
    <p class="sr-only" role="status" aria-live="polite">{{ rotaAnunciada() }}</p>

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
            <span class="fi-wordmark">fiance</span>
          </a>

          <nav class="hidden lg:block" aria-label="Navegação principal">
            <ul class="flex items-center gap-1 list-none m-0 p-0">
              @for (d of destinations; track d.path) {
                <li>
                  <a
                    [routerLink]="d.path"
                    routerLinkActive="nav-active"
                    #rla="routerLinkActive"
                    [attr.aria-current]="rla.isActive ? 'page' : null"
                    class="nav-link"
                  >
                    <lucide-icon [name]="d.icon" size="16"></lucide-icon>
                    {{ d.label }}
                  </a>
                </li>
              }
            </ul>
          </nav>

          <div class="flex items-center gap-2">
            @if (direitos.inTrial() && direitos.trialDaysLeft() !== null) {
              <a
                routerLink="/voce/conta"
                class="hidden sm:inline-flex items-center h-9 px-2.5 rounded-md no-underline border fi-caption"
                [class.border-hairline]="!direitos.trialEndingSoon()"
                [class.text-ink-2]="!direitos.trialEndingSoon()"
                [class.border-attention]="direitos.trialEndingSoon()"
                [class.text-attention]="direitos.trialEndingSoon()"
                [attr.aria-label]="rotuloDoTrial()"
              >
                {{ rotuloDoTrial() }}
              </a>
            }
            <button
              class="btn-secondary compact-btn hidden sm:inline-flex"
              type="button"
              (click)="search.show()"
              aria-label="Buscar tela ou ativo"
            >
              <lucide-icon name="search" size="16"></lucide-icon>
              <kbd class="fi-caption border border-hairline rounded-sm px-1">{{ searchHint }}</kbd>
            </button>
            <button
              class="btn-icon"
              type="button"
              (click)="activity.show()"
              title="Atividade recente"
              aria-label="Abrir atividade recente"
            >
              <lucide-icon name="history" size="18"></lucide-icon>
            </button>
            <button
              class="btn-icon"
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
              class="btn-icon btn-icon-quiet overflow-hidden rounded-pill p-0"
              (click)="showProfile.set(true)"
              title="Sua conta"
              aria-label="Abrir sua conta"
            >
              <img
                [src]="user.picture"
                [alt]="user.name"
                class="w-full h-full rounded-pill object-cover"
                referrerpolicy="no-referrer"
              />
            </button>
          </div>
        </div>
      </header>
    }

    <main class="max-w-dense mx-auto px-3 sm:px-5 pt-5 sm:pt-6 pb-24 lg:pb-10">
      <router-outlet />
    </main>

    @if (auth.user()) {
      <nav
        class="lg:hidden fixed bottom-0 left-0 right-0 border-t border-hairline bg-ground-1"
        style="padding-bottom: env(safe-area-inset-bottom); z-index: var(--fi-z-nav);"
        aria-label="Navegação principal"
      >
        <ul class="flex items-stretch justify-around h-14 list-none m-0 p-0">
          @for (d of destinations; track d.path) {
            <li class="flex-1 flex">
              <a
                [routerLink]="d.path"
                routerLinkActive="nav-active-mob"
                #rlaMob="routerLinkActive"
                [attr.aria-current]="rlaMob.isActive ? 'page' : null"
                class="fi-label flex flex-col items-center justify-center gap-0.5 px-1 flex-1 text-ink-2 no-underline transition-colors"
              >
                <lucide-icon [name]="d.icon" size="20"></lucide-icon>
                <span>{{ d.label }}</span>
              </a>
            </li>
          }
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
    void this.auth.logout();
    this.router.navigateByUrl('/login');
  }

  private _navShown = false;
  private _navTimer: ReturnType<typeof setTimeout> | null = null;

  private readonly densidade = inject(DensityService);
  readonly direitos = inject(EntitlementService);

  rotuloDoTrial(): string {
    const dias = this.direitos.trialDaysLeft();
    if (dias === null) return '';
    if (dias <= 0) return 'Teste acaba hoje';
    if (dias === 1) return 'Teste acaba amanhã';
    return `Teste: ${dias} dias`;
  }

  readonly rotaAnunciada = signal('');

  constructor() {
    this.densidade.ensureLoaded();
    this.direitos.ensureLoaded();

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
        if (e instanceof NavigationEnd) this.anunciarRota(e.urlAfterRedirects);
      }
    });
  }

  /** O nome da tela, dito depois de chegar nela. */
  private anunciarRota(url: string): void {
    const caminho = '/' + (url.split('?')[0].split('#')[0].split('/')[1] ?? '');
    const destino = DESTINATIONS.find(d => d.path === caminho);
    const nome = destino?.label ?? (caminho === '/ativo' ? 'Ativo' : 'fiance');

    // Limpar antes força o leitor a reler quando o destino é o mesmo de antes.
    this.rotaAnunciada.set('');
    queueMicrotask(() => this.rotaAnunciada.set(`${nome}. Tela carregada.`));
  }
}
