import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';
import { DashboardResponse, RecommendService, WhatsNewResponse } from '../../core';
import { DashboardComponent } from './dashboard.component';

const recommendStub = {
  getDashboard: () => ({ subscribe: () => undefined }),
  getWhatsNew: () => ({ subscribe: () => undefined }),
};

function dashboard(over: Partial<DashboardResponse> = {}): DashboardResponse {
  return {
    summary: {
      total_invested: 1000,
      total_current: 1100,
      total_pnl: 100,
      total_pnl_pct: 10,
      positions_count: 6,
      ...(over.summary ?? {}),
    },
    health: { score: 80, warnings: [], ...(over.health ?? {}) },
    alerts: over.alerts ?? [],
    allocations: over.allocations ?? [],
    top_buys: over.top_buys ?? [],
    top_sells: over.top_sells ?? [],
  } as unknown as DashboardResponse;
}

describe('Hoje', () => {
  let component: DashboardComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: RecommendService, useValue: recommendStub }],
    });
    component = TestBed.createComponent(DashboardComponent).componentInstance;
  });

  describe('veredito de saúde', () => {
    it('carteira pequena não recebe veredito, recebe a razão de não ter', () => {
      component.data.set(dashboard({ summary: { positions_count: 3 } as never }));

      expect(component.healthReliability()).toBe(0);
      expect(component.healthVerdict()).toContain('pequena');
      expect(component.healthReasons()[0]).toContain('3 ativos');
    });

    it('o singular do motivo acompanha a contagem', () => {
      component.data.set(dashboard({ summary: { positions_count: 1 } as never }));

      expect(component.healthReasons()[0]).toContain('1 ativo,');
    });

    it('a partir de quatro ativos o veredito vem da faixa da régua', () => {
      component.data.set(dashboard({ summary: { positions_count: 4 } as never }));

      expect(component.healthReliability()).toBe(1);
      expect(component.healthVerdict()).toBe('Carteira saudável');

      component.data.set(
        dashboard({ summary: { positions_count: 4 } as never, health: { score: 10 } as never })
      );
      expect(component.healthVerdict()).not.toBe('Carteira saudável');
    });

    it('concentração vira motivo apenas acima do limiar que a torna relevante', () => {
      component.data.set(
        dashboard({
          health: {
            score: 60,
            warnings: [],
            top_position_ticker: 'PETR4',
            top_position_pct: 14.9,
          } as never,
        })
      );
      expect(component.healthReasons().some(r => r.includes('PETR4'))).toBe(false);

      component.data.set(
        dashboard({
          health: {
            score: 60,
            warnings: [],
            top_position_ticker: 'PETR4',
            top_position_pct: 15,
          } as never,
        })
      );
      expect(component.healthReasons().some(r => r.includes('PETR4'))).toBe(true);
    });

    it('carteira sem ponto de risco diz isso, em vez de ficar em branco', () => {
      component.data.set(dashboard());

      expect(component.healthReasons()).toHaveLength(1);
      expect(component.healthReasons()[0]).toContain('Nenhum ponto');
    });

    it('no máximo três motivos, para o veredito continuar legível', () => {
      component.data.set(
        dashboard({
          health: {
            score: 40,
            top_position_ticker: 'PETR4',
            top_position_pct: 30,
            top_sector: 'Bancos',
            top_sector_pct: 55,
            warnings: ['a', 'b', 'c', 'd'],
          } as never,
        })
      );

      expect(component.healthReasons()).toHaveLength(3);
    });
  });

  describe('feed', () => {
    it('o crítico vem antes do aviso, e o aviso antes do informativo', () => {
      component.data.set(
        dashboard({
          alerts: [
            { title: 'informativo', detail: '', severity: 'info', count: 1 },
            { title: 'crítico', detail: '', severity: 'critical', count: 1 },
            { title: 'aviso', detail: '', severity: 'warning', count: 1 },
          ] as never,
        })
      );

      expect(component.feed().map(i => i.title)).toEqual(['crítico', 'aviso', 'informativo']);
    });

    it('severidade vira estado, não cor escrita à mão', () => {
      component.data.set(
        dashboard({
          alerts: [
            { title: 'a', detail: '', severity: 'critical', count: 1 },
            { title: 'b', detail: '', severity: 'warning', count: 1 },
            { title: 'c', detail: '', severity: 'info', count: 1 },
          ] as never,
        })
      );

      expect(component.feed().map(i => i.state)).toEqual(['adverse', 'attention', 'neutral']);
    });

    it('alerta agrupado mostra a contagem no título', () => {
      component.data.set(
        dashboard({
          alerts: [{ title: 'Queda forte', detail: '', severity: 'warning', count: 3 }] as never,
        })
      );

      expect(component.feed()[0].title).toBe('Queda forte (3)');
    });

    it('o feed é limitado, senão vira lista de tudo que aconteceu', () => {
      component.data.set(
        dashboard({
          alerts: Array.from({ length: 12 }, (_, i) => ({
            title: `a${i}`,
            detail: '',
            severity: 'info',
            count: 1,
          })) as never,
        })
      );

      expect(component.feed().length).toBeLessThanOrEqual(6);
    });

    it('sinal de venda entra como um item só, com o plural certo', () => {
      component.data.set(dashboard({ top_sells: [{ ticker: 'AAAA3' }] as never }));
      expect(component.feed()[0].title).toContain('1 posição com sinal');

      component.data.set(
        dashboard({ top_sells: [{ ticker: 'AAAA3' }, { ticker: 'BBBB4' }] as never })
      );
      expect(component.feed()[0].title).toContain('2 posições com sinal');
    });

    it('meta batida é estado favorável; meta em curso é neutra', () => {
      const comProgresso = (progress: number) =>
        dashboard({
          summary: {
            positions_count: 6,
            passive_income_goal: 1000,
            passive_income_progress: progress,
            monthly_dividends_estimate: 500,
          } as never,
        });

      component.data.set(comProgresso(50));
      expect(component.feed()[0].state).toBe('neutral');

      component.data.set(comProgresso(100));
      expect(component.feed()[0].state).toBe('favorable');
    });

    it('sem dado nenhum o feed é vazio, não uma lista de vazios', () => {
      expect(component.feed()).toEqual([]);
    });

    it('novidade do período entra no feed junto dos alertas', () => {
      component.whatsNew.set({
        items: [
          { kind: 'empty', title: 'ignorar', detail: '', severity: 'info' },
          { kind: 'move', title: 'Subiu 8%', detail: '', severity: 'positive', ticker: 'PETR4' },
        ],
      } as unknown as WhatsNewResponse);

      const feed = component.feed();
      expect(feed).toHaveLength(1);
      expect(feed[0].state).toBe('favorable');
    });
  });

  describe('maior desvio de alocação', () => {
    it('desvio menor que dois pontos não vira próxima ação', () => {
      component.data.set(
        dashboard({
          allocations: [
            { category: 'acoes_br', current_pct: 51, target_pct: 50, delta_pct: 1 },
          ] as never,
        })
      );

      expect(component.biggestGap()).toBeNull();
    });

    it('entre dois desvios, ganha o maior em módulo — falta ou sobra', () => {
      component.data.set(
        dashboard({
          allocations: [
            { category: 'acoes_br', current_pct: 55, target_pct: 50, delta_pct: 5 },
            { category: 'fiis', current_pct: 12, target_pct: 20, delta_pct: -8 },
          ] as never,
        })
      );

      const gap = component.biggestGap();
      expect(gap?.absDelta).toBe(8);
      expect(gap?.below).toBe(true);
    });

    it('categoria sem meta definida não é desvio de nada', () => {
      component.data.set(
        dashboard({
          allocations: [
            { category: 'acoes_br', current_pct: 90, target_pct: null, delta_pct: null },
          ] as never,
        })
      );

      expect(component.biggestGap()).toBeNull();
    });
  });
});
