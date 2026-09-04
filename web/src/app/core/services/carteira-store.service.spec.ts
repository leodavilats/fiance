import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';
import { of } from 'rxjs';
import { FixedIncomeListResponse, PortfolioEvaluationResponse, PortfolioPosition } from '../models';
import { CarteiraStore, MAX_COMPARE } from './carteira-store.service';
import { RecommendService } from './recommend.service';

function position(over: Partial<PortfolioPosition> & { ticker: string }): PortfolioPosition {
  return {
    asset_type: 'br_stock',
    category_resolved: 'acoes_br',
    quantity: 100,
    avg_price: 10,
    invested: 1000,
    current_price: 12,
    current_value: 1200,
    pnl: 200,
    pnl_pct: 20,
    fair_price: 15,
    verdict: 'comprar',
    score: 70,
    sector: 'Bancos',
    dividend_yield: 6,
    ...over,
  } as PortfolioPosition;
}

function evaluation(positions: PortfolioPosition[]): PortfolioEvaluationResponse {
  const invested = positions.reduce((s, p) => s + p.invested, 0);
  const current = positions.reduce((s, p) => s + (p.current_value ?? p.invested), 0);
  return {
    positions,
    total_invested: invested,
    total_current: current,
  } as PortfolioEvaluationResponse;
}

/** O serviço só é tocado no `reload`, que estes testes não exercitam. */
const recommendStub = {
  getFixedIncome: () => of({ items: [], total_investido: 0, total_atual: 0 }),
  getClosedTrades: () => of({ trades: [] }),
  getDividendsReceived: () => of({ items: [] }),
  getGoals: () => of([]),
  getSectorGoals: () => of([]),
};

describe('CarteiraStore', () => {
  let store: CarteiraStore;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [{ provide: RecommendService, useValue: recommendStub }],
    });
    store = TestBed.inject(CarteiraStore);
  });

  it('soma renda fixa ao patrimônio, e não só as posições negociadas', () => {
    store.evaluation.set(evaluation([position({ ticker: 'PETR4' })]));
    store.fixedIncome.set({
      items: [],
      total_investido: 500,
      total_atual: 560,
    } as unknown as FixedIncomeListResponse);

    expect(store.totalInvestido()).toBe(1500);
    expect(store.valorAtual()).toBe(1760);
    expect(store.rendimentoTotal()).toBe(260);
    expect(store.rendimentoPct()).toBeCloseTo((260 / 1500) * 100, 6);
  });

  it('carteira sem nada investido não divide por zero', () => {
    expect(store.rendimentoPct()).toBe(0);
  });

  it('ordena por valor decrescente por padrão e inverte no mesmo clique', () => {
    store.evaluation.set(
      evaluation([
        position({ ticker: 'AAA', current_value: 100 }),
        position({ ticker: 'ZZZ', current_value: 900 }),
      ])
    );

    expect(store.tradedPositions().map(p => p.ticker)).toEqual(['ZZZ', 'AAA']);

    store.toggleSort('current_value');
    expect(store.tradedPositions().map(p => p.ticker)).toEqual(['AAA', 'ZZZ']);
  });

  it('trocar de coluna escolhe a direção que faz sentido para o tipo', () => {
    store.toggleSort('ticker');
    expect(store.sortDirection()).toBe('asc');

    store.toggleSort('pnl_pct');
    expect(store.sortDirection()).toBe('desc');
  });

  it('a comparação para no teto e não perde a seleção anterior', () => {
    for (const ticker of ['A', 'B', 'C', 'D', 'E']) store.toggleSelection(ticker);

    expect(store.selectedTickers()).toHaveLength(MAX_COMPARE);
    expect(store.isSelected('E')).toBe(false);

    store.toggleSelection('A');
    expect(store.isSelected('A')).toBe(false);
    expect(store.selectedTickers()).toHaveLength(MAX_COMPARE - 1);
  });

  /**
   * A alocação por categoria não é mais calculada aqui.
   *
   * O cliente somava as posições e dividia pelo total enquanto o backend fazia
   * a mesma conta para /hoje e /estrategia — duas verdades sobre o mesmo
   * número, e nada garantia que batessem. O store agora só ordena o que o
   * servidor apurou, e é isso que estes testes cobrem.
   */
  it('a alocação por tipo é a que o backend apurou, ordenada por valor', () => {
    store.alocacaoOficial.set([
      {
        category: 'renda_fixa',
        current_value: 250,
        current_pct: 25,
        target_pct: null,
        delta_pct: null,
        delta_value: null,
      },
      {
        category: 'acoes_br',
        current_value: 750,
        current_pct: 75,
        target_pct: null,
        delta_pct: null,
        delta_value: null,
      },
    ]);

    const porTipo = store.alocacaoPorTipo();

    expect(porTipo.map(t => t.tipo)).toEqual(['acoes_br', 'renda_fixa']);
    expect(porTipo.find(t => t.tipo === 'renda_fixa')?.pct).toBeCloseTo(25, 6);
    expect(porTipo.reduce((s, t) => s + t.pct, 0)).toBeCloseTo(100, 6);
  });

  it('a meta da categoria vem junto da alocação, não de uma segunda conta', () => {
    store.alocacaoOficial.set([
      {
        category: 'acoes_br',
        current_value: 1000,
        current_pct: 100,
        target_pct: 60,
        delta_pct: 40,
        delta_value: 400,
      },
    ]);

    expect(store.alocacaoPorTipo()[0].targetPct).toBe(60);
  });

  it('sem resposta do servidor a alocação fica vazia, não estimada', () => {
    store.evaluation.set(evaluation([position({ ticker: 'PETR4', current_value: 750 })]));

    expect(store.alocacaoPorTipo()).toEqual([]);
  });

  it('a composição por setor agrupa a cauda em Outros sem perder valor', () => {
    const setores = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8'];
    store.evaluation.set(
      evaluation(
        setores.map((setor, i) =>
          position({ ticker: `T${i}`, sector: setor, current_value: 100 - i })
        )
      )
    );

    const porSetor = store.alocacaoPorSetor();

    expect(porSetor).toHaveLength(6);
    expect(porSetor.some(s => s.setor === 'Outros')).toBe(true);
    expect(porSetor.reduce((s, e) => s + e.pct, 0)).toBeCloseTo(100, 6);
  });

  it('a carteira só é vazia quando não há negociado nem renda fixa', () => {
    expect(store.isEmpty()).toBe(true);

    store.fixedIncome.set({
      items: [{ oculto: false }],
      total_investido: 1,
      total_atual: 1,
    } as unknown as FixedIncomeListResponse);

    expect(store.isEmpty()).toBe(false);
  });

  it('renda fixa oculta sai da lista mas continua no patrimônio', () => {
    store.fixedIncome.set({
      items: [{ oculto: false }, { oculto: true }],
      total_investido: 100,
      total_atual: 110,
    } as unknown as FixedIncomeListResponse);

    expect(store.fixedIncomePositions()).toHaveLength(1);
    expect(store.hiddenFixedIncome()).toHaveLength(1);
    expect(store.valorAtual()).toBe(110);
  });

  it('a renda mensal estimada soma dividendos e renda fixa, em mês', () => {
    store.evaluation.set(
      evaluation([position({ ticker: 'PETR4', current_value: 1200, dividend_yield: 12 })])
    );
    store.fixedIncome.set({
      items: [{ oculto: false, valor_atual: 1000, yield_equivalente_pct: 12 }],
      total_investido: 1000,
      total_atual: 1000,
    } as unknown as FixedIncomeListResponse);

    expect(store.estimatedMonthlyIncome()).toBe(22);
  });

  it('sem rendimento nenhum, a estimativa é nula em vez de zero', () => {
    expect(store.estimatedMonthlyIncome()).toBeNull();
  });

  describe('lista cortada pela paginação', () => {
    it('nada cortado não vira aviso', () => {
      store.fixedIncome.set({
        items: [],
        total_investido: 0,
        total_atual: 0,
        has_more: false,
      } as unknown as FixedIncomeListResponse);

      expect(store.truncated()).toEqual([]);
    });

    it('cada lista cortada aparece pelo nome', () => {
      store.fixedIncome.set({
        items: [],
        total_investido: 0,
        total_atual: 0,
        has_more: true,
      } as unknown as FixedIncomeListResponse);
      store.closedTrades.set({ trades: [], has_more: true } as never);

      expect(store.truncated()).toEqual(['operações encerradas', 'renda fixa']);
    });

    it('resposta sem o campo não é tratada como cortada', () => {
      store.closedTrades.set({ trades: [] } as never);

      expect(store.truncated()).toEqual([]);
    });
  });
});
