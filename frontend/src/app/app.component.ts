import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { ThemeService } from './core';
import {
  AnalyzeComponent,
  AssetsComponent,
  ConfigComponent,
  DashboardComponent,
  DipComponent,
  DividendsComponent,
  GlobalLoaderComponent,
  OpportunitiesComponent,
  SnackbarComponent,
  StrategyComponent,
} from './components';

type Tab = 'dashboard' | 'assets' | 'opportunities' | 'dividends' | 'analyze' | 'dip' | 'strategy' | 'config';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    LucideAngularModule,
    AnalyzeComponent,
    AssetsComponent,
    ConfigComponent,
    DashboardComponent,
    DipComponent,
    DividendsComponent,
    GlobalLoaderComponent,
    OpportunitiesComponent,
    SnackbarComponent,
    StrategyComponent,
  ],
  template: `
    <app-global-loader />
    <app-snackbar />
    <div class="max-w-[1180px] mx-auto px-5 pt-6 pb-10">
      <header class="flex justify-between items-center gap-4 py-2 px-1 pb-[18px]">
        <div style="display:flex; align-items:center; gap:14px;">
          <div class="w-11 h-11 grid place-items-center rounded-xl font-extrabold text-[1.4rem] text-[#0b0e14] bg-gradient-to-br from-accent to-accent-2">f</div>
          <div>
            <h1 class="text-[1.7rem] font-bold m-0 text-tx">fianceAI</h1>
            <p class="m-0 text-sm text-muted">Sistema de gestão de ativos — descubra o que comprar, manter ou vender.</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button class="w-9 h-9 grid place-items-center rounded-lg cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel hover:opacity-90 transition-opacity" type="button" (click)="theme.toggle()" [title]="theme.theme() === 'dark' ? 'Modo claro' : 'Modo escuro'">
            <lucide-icon [name]="theme.theme() === 'dark' ? 'sun' : 'moon'" size="18"></lucide-icon>
          </button>
        </div>
      </header>
      <nav class="flex flex-wrap gap-2 mb-6">
        <button type="button" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all" [class.active]="tab() === 'dashboard'" (click)="tab.set('dashboard')">
          <lucide-icon name="layout-dashboard" size="16"></lucide-icon> Dashboard
        </button>
        <button type="button" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all" [class.active]="tab() === 'assets'" (click)="tab.set('assets')">
          <lucide-icon name="briefcase" size="16"></lucide-icon> Meus Ativos
        </button>
        <button type="button" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all" [class.active]="tab() === 'opportunities'" (click)="tab.set('opportunities')">
          <lucide-icon name="target" size="16"></lucide-icon> Oportunidades
        </button>
        <button type="button" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all" [class.active]="tab() === 'dividends'" (click)="tab.set('dividends')">
          <lucide-icon name="dollar-sign" size="16"></lucide-icon> Dividendos
        </button>
        <button type="button" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all" [class.active]="tab() === 'analyze'" (click)="tab.set('analyze')">
          <lucide-icon name="search" size="16"></lucide-icon> Analisar
        </button>
        <button type="button" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all" [class.active]="tab() === 'dip'" (click)="tab.set('dip')">
          <lucide-icon name="trending-down" size="16"></lucide-icon> Na Baixa?
        </button>
        <button type="button" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all" [class.active]="tab() === 'strategy'" (click)="tab.set('strategy')">
          <lucide-icon name="wand-sparkles" size="16"></lucide-icon> Estratégia
        </button>
        <button type="button" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all" [class.active]="tab() === 'config'" (click)="tab.set('config')">
          <lucide-icon name="settings" size="16"></lucide-icon> Configurações
        </button>
      </nav>
      @if (tab() === 'dashboard') { <app-dashboard /> }
      @if (tab() === 'assets') { <app-assets /> }
      @if (tab() === 'opportunities') { <app-opportunities /> }
      @if (tab() === 'strategy') { <app-strategy /> }
      @if (tab() === 'dividends') { <app-dividends /> }
      @if (tab() === 'analyze') { <app-analyze /> }
      @if (tab() === 'dip') { <app-dip /> }
      @if (tab() === 'config') { <app-config /> }
    </div>
  `,
})
export class AppComponent {
  readonly theme = inject(ThemeService);
  readonly tab = signal<Tab>('dashboard');
}
