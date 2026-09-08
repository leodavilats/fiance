import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./components/login/login.component').then(m => m.LoginComponent),
    title: 'Entrar - fiance',
  },
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () =>
      import('./components/landing/landing.component').then(m => m.LandingComponent),
    title: 'fiance — o seu mês e o seu investimento no mesmo lugar',
  },

  {
    path: 'mes/atividade',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/activity/activity-page.component').then(m => m.ActivityPageComponent),
    title: 'Atividade - fiance',
  },

  {
    path: 'mes',
    canActivate: [authGuard],
    loadComponent: () => import('./components/month/month.component').then(m => m.MonthComponent),
    title: 'Mês - fiance',
  },
  {
    path: 'mes/lancar',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/month-entry/month-entry.component').then(m => m.MonthEntryComponent),
    title: 'Lançar no mês - fiance',
  },
  {
    path: 'mes/repetir',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/month-template/month-template.component').then(
        m => m.MonthTemplateComponent
      ),
    title: 'Repetir o mês - fiance',
  },
  {
    path: 'mes/dividas',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/month-debts/month-debts.component').then(m => m.MonthDebtsComponent),
    title: 'Dívidas - fiance',
  },
  {
    path: 'patrimonio',
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
    path: 'sobra',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/shell/strategy-shell.component').then(m => m.StrategyShellComponent),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./components/surplus/surplus.component').then(m => m.SurplusComponent),
        title: 'Sobra - fiance',
      },
      {
        path: 'desvio',
        loadComponent: () =>
          import('./components/strategy/strategy.component').then(m => m.StrategyComponent),
        title: 'Alocação × meta - fiance',
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

  {
    path: 'termos',
    loadComponent: () => import('./components/legal/terms.component').then(m => m.TermsComponent),
    title: 'Termos de Uso - fiance',
  },
  {
    path: 'privacidade',
    loadComponent: () =>
      import('./components/legal/privacy.component').then(m => m.PrivacyComponent),
    title: 'Política de Privacidade - fiance',
  },
  {
    path: 'aviso-cvm',
    loadComponent: () => import('./components/legal/cvm.component').then(m => m.CvmNoticeComponent),
    title: 'Aviso CVM - fiance',
  },

  /*
   * As URLs da IA anterior, como redirect.
   *
   * Link salvo é contrato, e a transição anterior (Mercado/Meus Ativos → cinco destinos) já
   * seguiu esta regra. `hoje` vai para `mes` porque é onde o "agora" mora agora; `estrategia`
   * vai para `patrimonio` porque, sem aporte, meta e projeção, o que sobrava dela era o desvio
   * de alocação — leitura de patrimônio.
   */
  { path: 'hoje', redirectTo: 'mes', pathMatch: 'full' },
  { path: 'hoje/atividade', redirectTo: 'mes/atividade', pathMatch: 'full' },
  { path: 'carteira', redirectTo: 'patrimonio', pathMatch: 'full' },
  { path: 'carteira/composicao', redirectTo: 'patrimonio/composicao', pathMatch: 'full' },
  { path: 'carteira/proventos', redirectTo: 'patrimonio/proventos', pathMatch: 'full' },
  { path: 'carteira/posicoes', redirectTo: 'patrimonio/posicoes', pathMatch: 'full' },
  { path: 'carteira/encerradas', redirectTo: 'patrimonio/encerradas', pathMatch: 'full' },
  { path: 'carteira/desempenho', redirectTo: 'patrimonio/desempenho', pathMatch: 'full' },
  { path: 'carteira/editar', redirectTo: 'patrimonio/editar', pathMatch: 'full' },
  { path: 'carteira/importar', redirectTo: 'patrimonio', pathMatch: 'full' },
  { path: 'carteira/transacoes', redirectTo: 'patrimonio', pathMatch: 'full' },
  { path: 'estrategia', redirectTo: 'sobra/desvio', pathMatch: 'full' },
  { path: 'estrategia/aporte', redirectTo: 'sobra/aporte', pathMatch: 'full' },
  { path: 'estrategia/metas', redirectTo: 'sobra/metas', pathMatch: 'full' },
  { path: 'estrategia/renda-fixa', redirectTo: 'sobra/renda-fixa', pathMatch: 'full' },
  { path: 'estrategia/projecao', redirectTo: 'sobra/projecao', pathMatch: 'full' },

  { path: 'dashboard', redirectTo: 'mes', pathMatch: 'full' },
  { path: 'assets', redirectTo: 'patrimonio', pathMatch: 'full' },
  { path: 'assets/cadastro', redirectTo: 'patrimonio/editar', pathMatch: 'full' },
  { path: 'market', redirectTo: 'descobrir/oportunidades', pathMatch: 'full' },
  { path: 'config', redirectTo: 'voce/preferencias', pathMatch: 'full' },
  { path: 'strategy', redirectTo: 'sobra/desvio', pathMatch: 'full' },

  { path: '**', redirectTo: 'mes' },
];
