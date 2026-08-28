import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { beforeEach, describe, expect, it } from 'vitest';
import { PendingDividend, RecommendService, SnackbarService } from '../../core';
import { ProventosPendentesComponent } from './proventos-pendentes.component';

function pendente(over: Partial<PendingDividend> = {}): PendingDividend {
  return {
    ticker: 'PETR4',
    paid_at: '2026-06-15',
    quantity_at_date: 100,
    rate_per_share: 0.5,
    amount: 50,
    kind: 'dividendo',
    caveats: ['A fonte publica a data de pagamento, não a data-com.'],
    quantity_is_current: false,
    ...over,
  };
}

function setup(items: PendingDividend[], options: { falha?: boolean } = {}) {
  const confirmados: unknown[][] = [];

  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [
      {
        provide: SnackbarService,
        useValue: { showSuccess: () => undefined, showError: () => undefined },
      },
      {
        provide: RecommendService,
        useValue: {
          getPendingDividends: () =>
            options.falha
              ? throwError(() => new Error('fora do ar'))
              : of({ items, count: items.length, note: 'Nada foi lançado.' }),
          confirmPendingDividends: (escolhidos: unknown[]) => {
            confirmados.push(escolhidos);
            return of({ created: escolhidos.length });
          },
        },
      },
    ],
  });

  const component = TestBed.createComponent(ProventosPendentesComponent).componentInstance;
  component.ngOnInit();
  return { component, confirmados };
}

describe('proventos pendentes', () => {
  beforeEach(() => TestBed.resetTestingModule());

  it('nada vem selecionado por padrão', () => {
    // Não há "aceitar todos": lançar em massa é o caminho para registrar
    // provento que a pessoa não recebeu.
    const { component } = setup([pendente(), pendente({ ticker: 'VALE3' })]);

    expect(component.selectedCount()).toBe(0);
  });

  it('confirmar sem seleção não chama o backend', () => {
    const { component, confirmados } = setup([pendente()]);

    component.confirm();

    expect(confirmados).toEqual([]);
  });

  it('só os selecionados são enviados', () => {
    const items = [pendente(), pendente({ ticker: 'VALE3', amount: 80 })];
    const { component, confirmados } = setup(items);

    component.toggle(items[1]);
    component.confirm();

    expect(confirmados).toHaveLength(1);
    expect(confirmados[0]).toHaveLength(1);
    expect((confirmados[0][0] as { ticker: string }).ticker).toBe('VALE3');
  });

  it('a chave distingue o mesmo ativo em datas diferentes', () => {
    const junho = pendente({ paid_at: '2026-06-15' });
    const julho = pendente({ paid_at: '2026-07-15' });
    const { component } = setup([junho, julho]);

    component.toggle(junho);

    expect(component.isSelected(junho)).toBe(true);
    expect(component.isSelected(julho)).toBe(false);
  });

  it('o total mostrado é o dos selecionados, não o da lista', () => {
    const items = [pendente({ amount: 50 }), pendente({ ticker: 'VALE3', amount: 80 })];
    const { component } = setup(items);

    component.toggle(items[0]);

    expect(component.selectedTotal()).toBe(50);
  });

  it('desmarcar tira da seleção', () => {
    const items = [pendente()];
    const { component } = setup(items);

    component.toggle(items[0]);
    component.toggle(items[0]);

    expect(component.selectedCount()).toBe(0);
  });

  it('sem pendências o painel não aparece', () => {
    const { component } = setup([]);

    expect(component.hasPending()).toBe(false);
  });

  it('backend fora do ar não deixa a tela carregando para sempre', () => {
    const { component } = setup([], { falha: true });

    expect(component.loading()).toBe(false);
    expect(component.hasPending()).toBe(false);
  });
});
