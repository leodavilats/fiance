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
      import('./components/activity/atividade-page.component').then(m => m.AtividadePageComponent),
    title: 'Atividade - fiance',
  },

  {
    path: 'carteira',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/shell/carteira.component').then(m => m.CarteiraComponent),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./components/carteira-resumo/carteira-resumo.component').then(
            m => m.CarteiraResumoComponent
          ),
        title: 'Carteira - fiance',
      },
      {
        path: 'composicao',
        loadComponent: () =>
          import('./components/composicao/composicao.component').then(m => m.ComposicaoComponent),
        title: 'Composição - fiance',
      },
      {
        path: 'proventos',
        loadComponent: () =>
          import('./components/proventos/proventos.component').then(m => m.ProventosComponent),
        title: 'Proventos - fiance',
      },
      {
        path: 'posicoes',
        loadComponent: () =>
          import('./components/posicoes/posicoes.component').then(m => m.PosicoesComponent),
        title: 'Posições - fiance',
      },
      {
        path: 'importar',
        loadComponent: () =>
          import('./components/importar/importar.component').then(m => m.ImportarComponent),
        title: 'Importar operações - fiance',
      },
      {
        path: 'transacoes',
        loadComponent: () =>
          import('./components/transacoes/transacoes.component').then(m => m.TransacoesComponent),
        title: 'Lançamentos - fiance',
      },
      {
        path: 'encerradas',
        loadComponent: () =>
          import('./components/encerradas/encerradas.component').then(m => m.EncerradasComponent),
        title: 'Operações encerradas - fiance',
      },
      {
        path: 'desempenho',
        loadComponent: () =>
          import('./components/desempenho/desempenho.component').then(m => m.DesempenhoComponent),
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
      import('./components/shell/descobrir.component').then(m => m.DescobrirComponent),
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
      import('./components/shell/estrategia.component').then(m => m.EstrategiaComponent),
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
          import('./components/metas/metas.component').then(m => m.MetasComponent),
        title: 'Metas - fiance',
      },
      {
        path: 'renda-fixa',
        loadComponent: () =>
          import('./components/shell/renda-fixa-page.component').then(
            m => m.RendaFixaPageComponent
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
    // Pública de propósito, e é a única. É o canal de aquisição do produto: o
    // modelo não comporta mídia paga, então a página de ativo precisa ser
    // legível por um robô de busca — e robô não faz login.
    path: 'ativo/:ticker',
    loadComponent: () => import('./components/ativo/ativo.component').then(m => m.AtivoComponent),
    title: 'Ativo - fiance',
  },
  {
    path: 'ativo',
    canActivate: [authGuard],
    loadComponent: () => import('./components/ativo/ativo.component').then(m => m.AtivoComponent),
    title: 'Ativo - fiance',
  },

  {
    path: 'voce',
    canActivate: [authGuard],
    loadComponent: () => import('./components/shell/voce.component').then(m => m.VoceComponent),
    children: [
      { path: '', redirectTo: 'preferencias', pathMatch: 'full' },
      {
        path: 'preferencias',
        loadComponent: () =>
          import('./components/preferencias/preferencias.component').then(
            m => m.PreferenciasComponent
          ),
        title: 'Preferências - fiance',
      },
      {
        path: 'alertas',
        loadComponent: () =>
          import('./components/alertas/alertas.component').then(m => m.AlertasComponent),
        title: 'Alertas - fiance',
      },
      {
        path: 'conta',
        loadComponent: () =>
          import('./components/conta/conta.component').then(m => m.ContaComponent),
        title: 'Conta e dados - fiance',
      },
    ],
  },

  { path: 'dashboard', redirectTo: 'hoje', pathMatch: 'full' },
  { path: 'assets', redirectTo: 'carteira', pathMatch: 'full' },
  { path: 'assets/cadastro', redirectTo: 'carteira/editar', pathMatch: 'full' },
  { path: 'market', redirectTo: 'descobrir/oportunidades', pathMatch: 'full' },
  { path: 'config', redirectTo: 'voce/preferencias', pathMatch: 'full' },
  { path: 'strategy', redirectTo: 'estrategia', pathMatch: 'full' },

  { path: '**', redirectTo: 'hoje' },
];
