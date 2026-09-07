import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { beforeEach, describe, expect, it } from 'vitest';
import { DashboardResponse, RecommendService, WhatsNewResponse } from '../../core';
import { MudouFeedComponent } from './mudou-feed.component';

/*
 * Os casos do feed vieram de `dashboard.component.spec.ts`, e continuam valendo: a tela mudou de
 * lugar, a regra de ordenação e de estado não. Dissolver `/hoje` sem trazer estes testes junto
 * teria apagado a cobertura da única lógica que a tela tinha de próprio.
 */

const recommendStub = {
  dashboard: () => ({ subscribe: () => undefined }),
  whatsNew: () => ({ subscribe: () => undefined }),
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

describe('o feed do que mudou', () => {
  let component: MudouFeedComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: RecommendService, useValue: recommendStub }],
    });
    component = TestBed.createComponent(MudouFeedComponent).componentInstance;
  });

  it('o crítico vem antes do aviso, e o aviso antes do informativo', () => {
    component.dados.set(
      dashboard({
        alerts: [
          { title: 'informativo', detail: '', severity: 'info', count: 1 },
          { title: 'crítico', detail: '', severity: 'critical', count: 1 },
          { title: 'aviso', detail: '', severity: 'warning', count: 1 },
        ] as never,
      })
    );

    expect(component.itens().map(i => i.title)).toEqual(['crítico', 'aviso', 'informativo']);
  });

  it('severidade vira estado, não cor escrita à mão', () => {
    component.dados.set(
      dashboard({
        alerts: [
          { title: 'a', detail: '', severity: 'critical', count: 1 },
          { title: 'b', detail: '', severity: 'warning', count: 1 },
          { title: 'c', detail: '', severity: 'info', count: 1 },
        ] as never,
      })
    );

    expect(component.itens().map(i => i.state)).toEqual(['adverse', 'attention', 'neutral']);
  });

  it('alerta agrupado mostra a contagem no título', () => {
    component.dados.set(
      dashboard({
        alerts: [{ title: 'Queda forte', detail: '', severity: 'warning', count: 3 }] as never,
      })
    );

    expect(component.itens()[0].title).toBe('Queda forte (3)');
  });

  it('o feed é limitado, senão vira lista de tudo que aconteceu', () => {
    component.dados.set(
      dashboard({
        alerts: Array.from({ length: 12 }, (_, i) => ({
          title: `a${i}`,
          detail: '',
          severity: 'info',
          count: 1,
        })) as never,
      })
    );

    expect(component.itens().length).toBeLessThanOrEqual(6);
  });

  it('sinal de venda entra como um item só, com o plural certo', () => {
    component.dados.set(dashboard({ top_sells: [{ ticker: 'AAAA3' }] as never }));
    expect(component.itens()[0].title).toContain('1 posição com sinal');

    component.dados.set(
      dashboard({ top_sells: [{ ticker: 'AAAA3' }, { ticker: 'BBBB4' }] as never })
    );
    expect(component.itens()[0].title).toContain('2 posições com sinal');
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

    component.dados.set(comProgresso(50));
    expect(component.itens()[0].state).toBe('neutral');

    component.dados.set(comProgresso(100));
    expect(component.itens()[0].state).toBe('favorable');
  });

  it('sem dado nenhum o feed é vazio, não uma lista de vazios', () => {
    component.dados.set(dashboard());

    expect(component.itens()).toEqual([]);
  });

  it('novidade do período entra no feed junto dos alertas', () => {
    component.dados.set(
      dashboard({
        alerts: [{ title: 'alerta', detail: '', severity: 'warning', count: 1 }] as never,
      })
    );
    component.mudou.set({
      days_since: 3,
      items: [
        { kind: 'dividend', title: 'novidade', detail: '', severity: 'positive', ticker: null },
      ],
    } as unknown as WhatsNewResponse);

    expect(component.itens().map(i => i.title)).toContain('novidade');
  });
});
