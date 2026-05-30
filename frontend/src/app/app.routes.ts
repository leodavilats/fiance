import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full',
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./components/dashboard/dashboard.component').then(m => m.DashboardComponent),
    title: 'Dashboard - fianceAI',
  },
  {
    path: 'assets',
    loadComponent: () =>
      import('./components/assets/assets.component').then(m => m.AssetsComponent),
    title: 'Meus Ativos - fianceAI',
  },
  {
    path: 'market',
    loadComponent: () =>
      import('./components/market/market.component').then(m => m.MarketComponent),
    title: 'Mercado - fianceAI',
  },
  {
    path: 'strategy',
    loadComponent: () =>
      import('./components/strategy/strategy.component').then(m => m.StrategyComponent),
    title: 'Estratégia - fianceAI',
  },
  {
    path: 'config',
    loadComponent: () =>
      import('./components/config/config.component').then(m => m.ConfigComponent),
    title: 'Configurações - fianceAI',
  },
  {
    path: '**',
    redirectTo: 'dashboard',
  },
];
