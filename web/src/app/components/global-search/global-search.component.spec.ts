import { importProvidersFrom, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import {
  ChartCandlestick,
  Landmark,
  LucideAngularModule,
  Search,
  Sunrise,
  Wallet,
} from 'lucide-angular';
import { beforeEach, describe, expect, it } from 'vitest';
import { GlobalSearchService } from '../../core';
import { GlobalSearchComponent } from './global-search.component';

type Grupo = {
  label: string;
  items: { kind: string; title: string; subtitle: string; ref: string }[];
};

function fakeSearch(
  options: { mine?: Grupo[]; tickers?: { ticker: string; name: string }[] } = {}
) {
  return {
    open: signal(true),
    query: signal('petr'),
    searching: signal(false),
    mine: signal(options.mine ?? []),
    tickers: signal(options.tickers ?? []),
    destinations: () => [
      { route: '/hoje', label: 'Hoje', section: 'Hoje', keywords: '', icon: 'sunrise' },
    ],
    show: () => undefined,
    hide: () => undefined,
    toggle: () => undefined,
    setQuery: () => undefined,
  };
}

function render(options: Parameters<typeof fakeSearch>[0] = {}) {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      importProvidersFrom(
        LucideAngularModule.pick({ ChartCandlestick, Landmark, Search, Sunrise, Wallet })
      ),
      { provide: GlobalSearchService, useValue: fakeSearch(options) },
    ],
  });
  const fixture = TestBed.createComponent(GlobalSearchComponent);
  fixture.detectChanges();
  return fixture;
}

const POSICAO: Grupo = {
  label: 'Na sua carteira',
  items: [
    {
      kind: 'position',
      title: 'PETR4',
      subtitle: '100 na carteira · preço médio R$ 30,00',
      ref: 'PETR4',
    },
  ],
};

const RENDA_FIXA: Grupo = {
  label: 'Sua renda fixa',
  items: [
    {
      kind: 'fixed_income',
      title: 'CDB Banco Inter',
      subtitle: 'CDB · aplicado em 2026-01-10',
      ref: '7',
    },
  ],
};

describe('busca global', () => {
  beforeEach(() => TestBed.resetTestingModule());

  describe('ordem da resposta', () => {
    it('o que é da pessoa vem antes das telas e do mercado', () => {
      const fixture = render({
        mine: [POSICAO],
        tickers: [{ ticker: 'PETR3', name: 'Petrobras' }],
      });
      const titulos = fixture.componentInstance.groups().map(g => g.title);

      expect(titulos[0]).toBe('Na sua carteira');
      expect(titulos.indexOf('Na sua carteira')).toBeLessThan(titulos.indexOf('Ativos'));
    });

    it('o rótulo do grupo vem do servidor, não é reescrito aqui', () => {
      const fixture = render({ mine: [POSICAO, RENDA_FIXA] });
      const titulos = fixture.componentInstance.groups().map(g => g.title);

      expect(titulos).toContain('Sua renda fixa');
    });
  });

  describe('a rota é decidida no cliente', () => {
    it('posição leva à página do ativo', () => {
      const fixture = render({ mine: [POSICAO] });
      const linha = fixture.componentInstance.rows()[0];

      expect(linha.route).toBe('/ativo/PETR4');
    });

    it('renda fixa leva às posições, não a uma página de ativo inexistente', () => {
      const fixture = render({ mine: [RENDA_FIXA] });
      const linha = fixture.componentInstance.rows()[0];

      expect(linha.route).toBe('/carteira/posicoes');
    });
  });

  describe('degradação', () => {
    it('sem resposta do servidor, as telas continuam navegáveis', () => {
      const fixture = render({ mine: [], tickers: [] });
      const titulos = fixture.componentInstance.groups().map(g => g.title);

      expect(titulos).toEqual(['Telas']);
      expect(fixture.componentInstance.rows().length).toBeGreaterThan(0);
    });
  });

  describe('teclado', () => {
    it('a lista é uma sequência única, mesmo dividida em seções', () => {
      const fixture = render({
        mine: [POSICAO],
        tickers: [{ ticker: 'PETR3', name: 'Petrobras' }],
      });
      const componente = fixture.componentInstance;

      const somaDasSecoes = componente.groups().reduce((total, g) => total + g.rows.length, 0);
      expect(componente.rows().length).toBe(somaDasSecoes);
    });
  });
});
