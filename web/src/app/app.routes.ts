import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./components/login/login.component').then(m => m.LoginComponent),
    title: 'Entrar - fiance',
  },
  { path: '', redirectTo: 'hoje', pathMatch: 'full' },

  {
    path: 'hoje',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/dashboard/dashboard.component').then(m => m.DashboardComponent),
    title: 'Hoje - fiance',
  },
  {
    path: 'hoje/atividade',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/activity/activity-page.component').then(m => m.ActivityPageComponent),
    title: 'Atividade - fiance',
  },

  {
    path: 'carteira',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/shell/portfolio-shell.component').then(m => m.PortfolioShellComponent),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./components/portfolio-summary/portfolio-summary.component').then(
            m => m.PortfolioSummaryComponent
          ),
        title: 'Carteira - fiance',
      },
      {
        path: 'composicao',
        loadComponent: () =>
          import('./components/composition/composition.component').then(
            m => m.CompositionComponent
          ),
        title: 'Composição - fiance',
      },
      {
        path: 'proventos',
        loadComponent: () =>
          import('./components/dividends/dividends.component').then(m => m.DividendsComponent),
        title: 'Proventos - fiance',
      },
      {
        path: 'posicoes',
        loadComponent: () =>
          import('./components/positions/positions.component').then(m => m.PositionsComponent),
        title: 'Posições - fiance',
      },
      {
        path: 'encerradas',
        loadComponent: () =>
          import('./components/closed-trades/closed-trades.component').then(
            m => m.ClosedTradesComponent
          ),
        title: 'Operações encerradas - fiance',
      },
      {
        path: 'desempenho',
        loadComponent: () =>
          import('./components/performance/performance.component').then(
            m => m.PerformanceComponent
          ),
        title: 'Desempenho - fiance',
      },
      {
        path: 'editar',
        loadComponent: () =>
          import('./components/portfolio-editor/portfolio-editor.component').then(
            m => m.PortfolioEditorComponent
          ),
        title: 'Editar carteira - fiance',
      },
    ],
  },

  {
    path: 'descobrir',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/shell/discover-shell.component').then(m => m.DiscoverShellComponent),
    children: [
      { path: '', redirectTo: 'oportunidades', pathMatch: 'full' },
      {
        path: 'oportunidades',
        loadComponent: () =>
          import('./components/market/opportunities-list/opportunities-list.component').then(
            m => m.OpportunitiesListComponent
          ),
        title: 'Oportunidades - fiance',
      },
      {
        path: 'quedas',
        loadComponent: () =>
          import('./components/market/dip-scanner/dip-scanner.component').then(
            m => m.DipScannerComponent
          ),
        title: 'Quedas - fiance',
      },
      {
        path: 'comparar',
        loadComponent: () =>
          import('./components/market/compare-assets/compare-assets.component').then(
            m => m.CompareAssetsComponent
          ),
        title: 'Comparar ativos - fiance',
      },
    ],
  },

  {
    path: 'estrategia',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/shell/strategy-shell.component').then(m => m.StrategyShellComponent),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./components/strategy/strategy.component').then(m => m.StrategyComponent),
        title: 'Estratégia - fiance',
      },
      {
        path: 'aporte',
        loadComponent: () =>
          import('./components/quick-invest/quick-invest.component').then(
            m => m.QuickInvestComponent
          ),
        title: 'Onde aportar - fiance',
      },
      {
        path: 'metas',
        loadComponent: () =>
          import('./components/goals/goals.component').then(m => m.GoalsComponent),
        title: 'Metas - fiance',
      },
      {
        path: 'renda-fixa',
        loadComponent: () =>
          import('./components/shell/fixed-income-page.component').then(
            m => m.FixedIncomePageComponent
          ),
        title: 'Renda fixa - fiance',
      },
      {
        path: 'projecao',
        loadComponent: () =>
          import('./components/market/contribution-simulator/contribution-simulator.component').then(
            m => m.ContributionSimulatorComponent
          ),
        title: 'Projeção - fiance',
      },
    ],
  },

  {
    path: 'ativo/:ticker',
    loadComponent: () => import('./components/asset/asset.component').then(m => m.AssetComponent),
    title: 'Ativo - fiance',
  },
  {
    path: 'ativo',
    canActivate: [authGuard],
    loadComponent: () => import('./components/asset/asset.component').then(m => m.AssetComponent),
    title: 'Ativo - fiance',
  },

  {
    path: 'voce',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/shell/you-shell.component').then(m => m.YouShellComponent),
    children: [
      { path: '', redirectTo: 'preferencias', pathMatch: 'full' },
      {
        path: 'preferencias',
        loadComponent: () =>
          import('./components/preferences/preferences.component').then(
            m => m.PreferencesComponent
          ),
        title: 'Preferências - fiance',
      },
      {
        path: 'alertas',
        loadComponent: () =>
          import('./components/price-alerts/price-alerts.component').then(
            m => m.PriceAlertsComponent
          ),
        title: 'Alertas - fiance',
      },
      {
        path: 'indicacao',
        loadComponent: () =>
          import('./components/referral/referral.component').then(m => m.ReferralComponent),
        title: 'Indicação - fiance',
      },
      {
        path: 'conta',
        loadComponent: () =>
          import('./components/account/account.component').then(m => m.AccountComponent),
        title: 'Conta e dados - fiance',
      },
    ],
  },

  { path: 'dashboard', redirectTo: 'hoje', pathMatch: 'full' },
  { path: 'carteira/importar', redirectTo: 'carteira', pathMatch: 'full' },
  { path: 'carteira/transacoes', redirectTo: 'carteira', pathMatch: 'full' },
  { path: 'assets', redirectTo: 'carteira', pathMatch: 'full' },
  { path: 'assets/cadastro', redirectTo: 'carteira/editar', pathMatch: 'full' },
  { path: 'market', redirectTo: 'descobrir/oportunidades', pathMatch: 'full' },
  { path: 'config', redirectTo: 'voce/preferencias', pathMatch: 'full' },
  { path: 'strategy', redirectTo: 'estrategia', pathMatch: 'full' },

  { path: '**', redirectTo: 'hoje' },
];
