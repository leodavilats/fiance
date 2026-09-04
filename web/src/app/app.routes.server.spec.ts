import { RenderMode } from '@angular/ssr';
import { describe, expect, it } from 'vitest';
import { routes } from './app.routes';
import { serverRoutes } from './app.routes.server';

describe('renderização no servidor', () => {
  it('só a página de ativo é renderizada no servidor', () => {
    const noServidor = serverRoutes
      .filter(route => route.renderMode === RenderMode.Server)
      .map(route => route.path);

    expect(noServidor).toEqual(['ativo/:ticker']);
  });

  it('todo o resto continua no cliente', () => {
    const coringa = serverRoutes.find(route => route.path === '**');

    expect(coringa?.renderMode).toBe(RenderMode.Client);
  });

  it('nenhuma rota de sessão é renderizada no servidor', () => {
    const deSessao = ['hoje', 'carteira', 'descobrir', 'estrategia', 'voce'];
    const paths = serverRoutes
      .filter(route => route.renderMode === RenderMode.Server)
      .map(route => route.path);

    for (const destino of deSessao) {
      expect(paths.some(path => path.startsWith(destino))).toBe(false);
    }
  });

  it('a rota do ativo não tem guarda de autenticação', () => {
    const ativo = routes.find(route => route.path === 'ativo/:ticker');

    expect(ativo).toBeDefined();
    expect(ativo?.canActivate).toBeUndefined();
  });

  it('as demais rotas de topo continuam protegidas', () => {
    const protegidas = ['hoje', 'carteira', 'descobrir', 'estrategia', 'voce'];

    for (const path of protegidas) {
      const route = routes.find(r => r.path === path);
      expect(route?.canActivate, path).toBeDefined();
    }
  });
});
