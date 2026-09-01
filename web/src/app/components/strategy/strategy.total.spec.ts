import { describe, expect, it } from 'vitest';
import { InvestmentStrategy, InvestmentSuggestion } from '../../core';
import { StrategyComponent } from './strategy.component';

function sugestao(invest_amount: number | null): InvestmentSuggestion {
  return {
    ticker: 'PETR4',
    name: 'Petrobras',
    asset_type: 'br_stock',
    category: 'acoes_br',
    objective: 'Crescimento',
    price: 38,
    quantity: invest_amount === null ? null : 13,
    invest_amount,
    score: 82,
    dividend_yield: null,
    margin_of_safety: null,
    verdict: 'BUY',
    already_held: false,
    reasons: [],
    transaction_cost: null,
  };
}

function estrategia(suggestions: InvestmentSuggestion[]): InvestmentStrategy {
  return {
    profile: {
      type: 'Moderado',
      description: '',
      goals: {},
      income_pct: 0,
      growth_pct: 0,
      risk_tolerance: 'Médio',
    },
    total_capital: 0,
    cash_available: 0,
    total_invested: 0,
    current_allocation: [],
    allocation_gaps: [],
    suggestions,
    reduce_suggestions: [],
    projected_allocation: [],
    summary: '',
  } as InvestmentStrategy;
}

describe('StrategyComponent.totalToInvest', () => {
  const componente = Object.create(StrategyComponent.prototype) as StrategyComponent;

  it('soma quando os valores chegam', () => {
    expect(componente.totalToInvest(estrategia([sugestao(494), sugestao(476)]))).toBe(970);
  });

  it('não soma quando o valor foi retido pela régua de afirmação', () => {
    expect(componente.totalToInvest(estrategia([sugestao(494), sugestao(null)]))).toBeNull();
  });
});
