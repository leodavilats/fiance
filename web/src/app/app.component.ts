import { CommonModule, DOCUMENT, isPlatformBrowser } from '@angular/common';
import { Component, PLATFORM_ID, inject, signal } from '@angular/core';
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
  WordmarkComponent,
} from './components';

interface NavDestination {
  readonly path: string;
  readonly label: string;
  readonly icon: string;
}

/** A navegação é o ciclo do dinheiro: renda → gasto → sobra → aporte → patrimônio. */
const DESTINATIONS: readonly NavDestination[] = [
  { path: '/mes', label: 'Mês', icon: 'calendar-clock' },
  { path: '/sobra', label: 'Sobra', icon: 'hand-coins' },
  { path: '/patrimonio', label: 'Patrimônio', icon: 'wallet' },
  { path: '/descobrir', label: 'Descobrir', icon: 'compass' },
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
    WordmarkComponent,
    ProfileModalComponent,
  ],
  template: `
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
          <a routerLink="/mes" class="flex items-center gap-2.5 no-underline" title="fiance">
            <app-logo [size]="30" />
            <app-wordmark [height]="18" [decorative]="true" />
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
                    class="nav-link fi-label"
                  >
                    <lucide-icon [name]="d.icon" size="16"></lucide-icon>
                    <span class="nav-label">
                      <span class="nav-label-text">{{ d.label }}</span>
                      <span class="nav-label-sizer" aria-hidden="true">{{ d.label }}</span>
                    </span>
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
              type="button"
              class="btn-icon btn-icon-quiet overflow-hidden rounded-pill p-0"
              (click)="showProfile.set(true)"
              title="Sua conta"
              aria-label="Abrir sua conta"
            >
              @if (user.picture) {
                <img
                  [src]="user.picture"
                  [alt]="user.name"
                  class="w-full h-full max-w-full rounded-pill object-cover"
                  referrerpolicy="no-referrer"
                />
              } @else {
                <span class="fi-label text-ink-2" aria-hidden="true">{{ inicial(user.name) }}</span>
              }
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
                class="fi-label flex flex-col items-center justify-center gap-0.5 px-1 flex-1 text-ink-2 no-underline transition-colors duration-base"
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
        position: relative;
        display: flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.5rem 0.75rem;
        color: var(--fi-ink-2);
        text-decoration: none;
        transition: color var(--fi-motion-base) var(--fi-motion-ease-enter);
      }
      .nav-link::after {
        content: '';
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 2px;
        background: var(--fi-brand);
        transform: scaleX(0);
        transition: transform var(--fi-motion-base) var(--fi-motion-ease-enter);
      }
      .nav-link:hover {
        color: var(--fi-ink-1);
      }
      .nav-label {
        display: inline-grid;
      }
      .nav-label-text,
      .nav-label-sizer {
        grid-area: 1 / 1;
      }
      .nav-label-sizer {
        font-weight: 600;
        visibility: hidden;
      }
      :host ::ng-deep a.nav-active {
        color: var(--fi-brand);
      }
      :host ::ng-deep a.nav-active::after {
        transform: scaleX(1);
      }
      :host ::ng-deep a.nav-active .nav-label-text {
        font-weight: 600;
      }
      :host ::ng-deep a.nav-active-mob {
        color: var(--fi-brand);
        font-weight: 600;
      }
      :host ::ng-deep a:focus-visible,
      :host ::ng-deep button:focus-visible {
        outline: var(--fi-focus-ring) solid var(--fi-brand);
        outline-offset: var(--fi-focus-offset);
      }
      a {
        text-decoration: none !important;
      }
      @media (prefers-reduced-motion: reduce) {
        .nav-link::after {
          transition: none;
        }
      }
    `,
  ],
})
export class AppComponent {
  readonly theme = inject(ThemeService);
  readonly auth = inject(AuthService);
  readonly search = inject(GlobalSearchService);
  readonly activity = inject(ActivityService);

  readonly searchHint = isPlatformBrowser(inject(PLATFORM_ID))
    ? /Mac|iPhone|iPad/.test(navigator.platform)
      ? '⌘K'
      : 'Ctrl K'
    : 'Ctrl K';
  readonly showProfile = signal(false);
  readonly destinations = DESTINATIONS;

  /*
   * Conta sem foto mostrava uma imagem quebrada.
   *
   * O `<img>` saia com `src` vazio, e o Chrome desenha o texto alternativo dentro do botao:
   * o avatar ficava 41px de largura numa caixa de 34 e o cabecalho vazava 3px em 320px de
   * viewport, nas cinco rotas. O teste de reflow nao pegava porque media antes de a imagem
   * resolver.
   */
  inicial(nome: string): string {
    return (nome || '?').trim().charAt(0).toUpperCase() || '?';
  }

  private readonly router = inject(Router);
  private readonly doc = inject(DOCUMENT);
  private readonly platformId = inject(PLATFORM_ID);
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
        if (e instanceof NavigationEnd) {
          this.anunciarRota(e.urlAfterRedirects);
          this.moverFocoParaOTitulo();
        }
      }
    });
  }

  private moverFocoParaOTitulo(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    queueMicrotask(() => {
      setTimeout(() => {
        const titulo = this.doc.querySelector<HTMLElement>('main h1');
        if (!titulo) return;

        // `focus()` em elemento sem `tabindex` nao faz nada, e nao avisa. Nove telas escrevem o
        // proprio `<h1>` em vez de usar `<app-page-header>`, e nelas a devolucao de foco falhava
        // calada. Quem devolve o foco e quem garante que o alvo o aceita.
        if (!titulo.hasAttribute('tabindex')) titulo.setAttribute('tabindex', '-1');
        titulo.focus({ preventScroll: true });
      }, 0);
    });
  }

  private anunciarRota(url: string): void {
    const caminho = '/' + (url.split('?')[0].split('#')[0].split('/')[1] ?? '');
    const destino = DESTINATIONS.find(d => d.path === caminho);
    const nome = destino?.label ?? (caminho === '/ativo' ? 'Ativo' : 'fiance');

    this.rotaAnunciada.set('');
    queueMicrotask(() => this.rotaAnunciada.set(`${nome}. Tela carregada.`));
  }
}
