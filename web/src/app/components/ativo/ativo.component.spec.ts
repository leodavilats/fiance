import { TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { provideRouter } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it } from 'vitest';
import { AssetAnalysis, AuthService, CarteiraStore, RecommendService } from '../../core';
import { AtivoComponent } from './ativo.component';

function analysis(over: Partial<AssetAnalysis> = {}): AssetAnalysis {
  return {
    symbol: 'PETR4',
    asset_type: 'br_stock',
    name: 'Petróleo Brasileiro S.A.',
    sector: 'Energia',
    currency: 'BRL',
    price: 42.7,
    fundamentals: {},
    fair_price: { consensus: 60.5 },
    technical: {},
    decision: { verdict: 'comprar', label: 'Comprar com convicção', confidence: 0.8, reasons: [] },
    price_history: [],
    ...over,
  } as unknown as AssetAnalysis;
}

const carteiraStub = { ensureLoaded: () => undefined };

function setup(options: { authenticated: boolean; asset: AssetAnalysis }) {
  const chamadas: string[] = [];

  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      { provide: ActivatedRoute, useValue: { paramMap: of(new Map([['ticker', 'petr4']])) } },
      { provide: CarteiraStore, useValue: carteiraStub },
      {
        provide: AuthService,
        useValue: { isAuthenticated: () => options.authenticated },
      },
      {
        provide: RecommendService,
        useValue: {
          analyzeAsset: (symbol: string) => {
            chamadas.push(symbol);
            return of(options.asset);
          },
          searchTickers: () => of({ items: [] }),
        },
      },
    ],
  });

  const fixture = TestBed.createComponent(AtivoComponent);
  fixture.componentInstance.ngOnInit();
  return { fixture, chamadas };
}

describe('página de ativo', () => {
  beforeEach(() => {
    document.head.querySelectorAll('link[rel="canonical"]').forEach(el => el.remove());
  });

  describe('metadados por ticker', () => {
    it('o título nomeia a empresa e o ticker, não uma categoria', () => {
      setup({ authenticated: false, asset: analysis() });

      const titulo = TestBed.inject(Title).getTitle();

      expect(titulo).toContain('Petróleo Brasileiro S.A.');
      expect(titulo).toContain('PETR4');
      expect(titulo).not.toBe('Ativo - fiance');
    });

    it('a descrição traz o veredito e os dois preços', () => {
      setup({ authenticated: false, asset: analysis() });

      const descricao =
        document.querySelector('meta[name="description"]')?.getAttribute('content') ?? '';

      expect(descricao).toContain('comprar com convicção');
      expect(descricao).toContain('60.50');
      expect(descricao).toContain('42.70');
    });

    it('dois tickers produzem descrições diferentes', () => {
      setup({ authenticated: false, asset: analysis() });
      const primeira = TestBed.inject(Title).getTitle();

      setup({
        authenticated: false,
        asset: analysis({ symbol: 'VALE3', name: 'Vale S.A.' }),
      });

      expect(TestBed.inject(Title).getTitle()).not.toBe(primeira);
    });

    it('a canônica é um link, é única e é absoluta', () => {
      setup({ authenticated: false, asset: analysis() });

      const canonicas = document.head.querySelectorAll('link[rel="canonical"]');

      expect(canonicas).toHaveLength(1);
      // Absoluta de propósito: uma canônica relativa resolve, mas não
      // normaliza host nem protocolo — que é o problema que ela existe para
      // resolver.
      expect(canonicas[0].getAttribute('href')).toBe(`${location.origin}/ativo/PETR4`);
    });

    it('o link compartilhado leva imagem e dado estruturado', () => {
      setup({ authenticated: false, asset: analysis() });

      const imagem = document.querySelector('meta[property="og:image"]')?.getAttribute('content');
      const card = document.querySelector('meta[name="twitter:card"]')?.getAttribute('content');
      const jsonld = document.head.querySelector('#fi-jsonld')?.textContent ?? '';

      expect(imagem).toContain('/public/asset/PETR4/og.png');
      expect(card).toBe('summary_large_image');
      expect(JSON.parse(jsonld).about.tickerSymbol).toBe('PETR4');
    });

    it('ativo sem preço justo ainda produz descrição legível', () => {
      setup({
        authenticated: false,
        asset: analysis({ fair_price: { consensus: null } as never }),
      });

      const descricao =
        document.querySelector('meta[name="description"]')?.getAttribute('content') ?? '';

      expect(descricao.length).toBeGreaterThan(40);
      expect(descricao).not.toContain('undefined');
      expect(descricao).not.toContain('NaN');
    });
  });

  describe('visitante anônimo', () => {
    it('não dispara o carregamento da carteira', () => {
      let carregou = false;
      TestBed.resetTestingModule();
      TestBed.configureTestingModule({
        providers: [
          provideRouter([]),
          { provide: ActivatedRoute, useValue: { paramMap: of(new Map([['ticker', 'petr4']])) } },
          { provide: CarteiraStore, useValue: { ensureLoaded: () => (carregou = true) } },
          { provide: AuthService, useValue: { isAuthenticated: () => false } },
          {
            provide: RecommendService,
            useValue: {
              analyzeAsset: () => of(analysis()),
              searchTickers: () => of({ items: [] }),
            },
          },
        ],
      });
      TestBed.createComponent(AtivoComponent).componentInstance.ngOnInit();

      expect(carregou).toBe(false);
    });

    it('com sessão, a carteira é carregada', () => {
      let carregou = false;
      TestBed.resetTestingModule();
      TestBed.configureTestingModule({
        providers: [
          provideRouter([]),
          { provide: ActivatedRoute, useValue: { paramMap: of(new Map([['ticker', 'petr4']])) } },
          { provide: CarteiraStore, useValue: { ensureLoaded: () => (carregou = true) } },
          { provide: AuthService, useValue: { isAuthenticated: () => true } },
          {
            provide: RecommendService,
            useValue: {
              analyzeAsset: () => of(analysis()),
              searchTickers: () => of({ items: [] }),
            },
          },
        ],
      });
      TestBed.createComponent(AtivoComponent).componentInstance.ngOnInit();

      expect(carregou).toBe(true);
    });
  });
});
