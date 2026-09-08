import { RenderMode } from '@angular/ssr';
import { describe, expect, it } from 'vitest';
import { routes } from './app.routes';
import { serverRoutes } from './app.routes.server';

describe('renderização no servidor', () => {
  it('a raiz, a página de ativo e o texto jurídico são o que roda no servidor', () => {
    const noServidor = serverRoutes
      .filter(route => route.renderMode === RenderMode.Server)
      .map(route => route.path);

    expect(noServidor).toEqual(['', 'ativo/:ticker', 'termos', 'privacidade', 'aviso-cvm']);
  });

  it('nenhuma rota pública do servidor tem guarda de autenticação', () => {
    const publicas = serverRoutes
      .filter(route => route.renderMode === RenderMode.Server)
      .map(route => route.path);

    for (const path of publicas) {
      const route = routes.find(r => r.path === path);
      expect(route, path).toBeDefined();
      expect(route?.canActivate, path).toBeUndefined();
    }
  });

  it('o texto jurídico existe como rota, senão a loja recebe URL quebrada', () => {
    for (const path of ['termos', 'privacidade', 'aviso-cvm']) {
      expect(
        routes.some(route => route.path === path),
        path
      ).toBe(true);
    }
  });

  it('todo o resto continua no cliente', () => {
    const coringa = serverRoutes.find(route => route.path === '**');

    expect(coringa?.renderMode).toBe(RenderMode.Client);
  });

  it('nenhuma rota de sessão é renderizada no servidor', () => {
    const deSessao = ['mes', 'sobra', 'patrimonio', 'descobrir', 'voce'];
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
    const protegidas = ['mes', 'sobra', 'patrimonio', 'descobrir', 'voce'];

    for (const path of protegidas) {
      const route = routes.find(r => r.path === path);
      expect(route?.canActivate, path).toBeDefined();
    }
  });

  it('as URLs da IA anterior continuam resolvendo', () => {
    const antigas: Record<string, string> = {
      hoje: 'mes',
      'hoje/atividade': 'mes/atividade',
      carteira: 'patrimonio',
      'carteira/posicoes': 'patrimonio/posicoes',
      'carteira/editar': 'patrimonio/editar',
      estrategia: 'sobra/desvio',
      'estrategia/aporte': 'sobra/aporte',
      // Sobra encolheu de seis subsecoes para tres, e estas tres mudaram de casa. O link
      // antigo continua resolvendo, e agora num salto so em vez de dois.
      'estrategia/metas': 'voce/objetivos',
      'estrategia/renda-fixa': 'descobrir/renda-fixa',
      'estrategia/projecao': 'patrimonio/projecao',
    };

    for (const [de, para] of Object.entries(antigas)) {
      const route = routes.find(r => r.path === de);
      expect(route, de).toBeDefined();
      expect(route?.redirectTo, de).toBe(para);
    }
  });

  it('o que saiu de Sobra continua resolvendo de dentro dela', () => {
    const sobra = routes.find(r => r.path === 'sobra');
    const filhos = sobra?.children ?? [];

    const mudaram: Record<string, string> = {
      metas: '/voce/objetivos',
      projecao: '/patrimonio/projecao',
      'renda-fixa': '/descobrir/renda-fixa',
    };

    for (const [de, para] of Object.entries(mudaram)) {
      const filho = filhos.find(r => r.path === de);
      expect(filho, `sobra/${de} deixou de existir sem redirect`).toBeDefined();
      expect(filho?.redirectTo, `sobra/${de}`).toBe(para);
    }

    const restantes = filhos
      .filter(r => !r.redirectTo)
      .map(r => r.path)
      .sort();
    expect(restantes, 'Sobra são os três passos de uma decisão só').toEqual([
      '',
      'aporte',
      'desvio',
    ]);
  });

  it('nenhum destino da IA nova ficou sem tela', () => {
    for (const destino of ['mes', 'sobra', 'patrimonio', 'descobrir', 'voce']) {
      const route = routes.find(r => r.path === destino);
      expect(route, destino).toBeDefined();
      expect(
        Boolean(route?.loadComponent || route?.children?.length),
        `${destino} precisa de componente ou de filhos`
      ).toBe(true);
    }
  });
});
