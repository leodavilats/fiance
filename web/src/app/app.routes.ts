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
    redirectTo: 'dashboard',
    pathMatch: 'full',
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/dashboard/dashboard.component').then(m => m.DashboardComponent),
    title: 'Dashboard - fiance',
  },
  {
    path: 'assets',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/assets/assets.component').then(m => m.AssetsComponent),
    title: 'Meus Ativos - fiance',
  },
  {
    path: 'market',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/market/market.component').then(m => m.MarketComponent),
    title: 'Mercado - fiance',
  },
  {
    path: 'config',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/config/config.component').then(m => m.ConfigComponent),
    title: 'Configurações - fiance',
  },
  {
    path: '**',
    redirectTo: 'dashboard',
  },
];
