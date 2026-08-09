import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./components/login/login.component').then(m => m.LoginComponent),
    title: 'Entrar - fianceAI',
  },
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full',
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/dashboard/dashboard.component').then(m => m.DashboardComponent),
    title: 'Dashboard - fianceAI',
  },
  {
    path: 'assets',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/assets/assets.component').then(m => m.AssetsComponent),
    title: 'Meus Ativos - fianceAI',
  },
  {
    path: 'market',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/market/market.component').then(m => m.MarketComponent),
    title: 'Mercado - fianceAI',
  },
  {
    path: 'config',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/config/config.component').then(m => m.ConfigComponent),
    title: 'Configurações - fianceAI',
  },
  {
    path: '**',
    redirectTo: 'dashboard',
  },
];
