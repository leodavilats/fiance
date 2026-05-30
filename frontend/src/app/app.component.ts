import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { ThemeService } from './core';
import { GlobalLoaderComponent, SnackbarComponent } from './components';

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
  ],
  template: `
    <app-global-loader />
    <app-snackbar />
    <div class="max-w-[1180px] mx-auto px-5 pt-6 pb-10">
      <header class="flex justify-between items-center gap-4 py-2 px-1 pb-[18px]">
        <div style="display:flex; align-items:center; gap:14px;">
          <div
            class="w-11 h-11 grid place-items-center rounded-xl font-extrabold text-[1.4rem] text-[#0b0e14] bg-gradient-to-br from-accent to-accent-2"
          >
            f
          </div>
          <div>
            <h1 class="text-[1.7rem] font-bold m-0 text-tx">fianceAI</h1>
            <p class="m-0 text-sm text-muted">
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
        </div>
      </header>
      <nav class="flex flex-wrap gap-2 mb-6">
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
          routerLink="/strategy"
          routerLinkActive="active"
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all no-underline"
        >
          <lucide-icon name="wand-sparkles" size="16"></lucide-icon> Estratégia
        </a>
        <a
          routerLink="/config"
          routerLinkActive="active"
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all no-underline"
        >
          <lucide-icon name="settings" size="16"></lucide-icon> Configurações
        </a>
      </nav>
      <router-outlet />
    </div>
  `,
  styles: [
    `
      :host ::ng-deep a.active {
        background: linear-gradient(135deg, #4ade80, #22d3ee);
        color: #0b0e14;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(34, 211, 238, 0.3);
      }

      a {
        text-decoration: none !important;
      }
    `,
  ],
})
export class AppComponent {
  readonly theme = inject(ThemeService);
}
