import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { QuickInvestResponse } from '../models';
import { RecommendService } from './recommend.service';

function montar() {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [provideHttpClient(), provideHttpClientTesting()],
  });
  return {
    svc: TestBed.inject(RecommendService),
    http: TestBed.inject(HttpTestingController),
  };
}

const RECUSA_DO_NULO = {
  detail: [
    {
      type: 'float_type',
      loc: ['body', 'cash_available'],
      msg: 'Input should be a valid number',
      input: null,
    },
  ],
};

describe('o aporte contra uma API anterior ao contrato', () => {
  beforeEach(() => TestBed.resetTestingModule());

  it('resolve a sobra no cliente quando a API recusa o nulo', () => {
    const { svc, http } = montar();
    const recebido = vi.fn<(r: QuickInvestResponse) => void>();

    svc.quickInvest({ cash_available: null, min_order_value: 50 }).subscribe(recebido);

    http
      .expectOne(r => r.url.endsWith('/quick-invest'))
      .flush(RECUSA_DO_NULO, { status: 422, statusText: 'Unprocessable Entity' });

    http
      .expectOne(r => r.url.endsWith('/surplus'))
      .flush({ cascade: { available_to_invest: 1240.5 } });

    const segunda = http.expectOne(r => r.url.endsWith('/quick-invest'));
    expect(
      segunda.request.body.cash_available,
      'o valor tem de sair da cascata, e não de um palpite do cliente'
    ).toBe(1240.5);

    segunda.flush({ total_cash: 1240.5, allocations: [], summary: 'ok' });

    expect(recebido).toHaveBeenCalledOnce();
    expect(
      recebido.mock.calls[0][0].cash_source,
      'a origem continua sendo a cascata, mesmo resolvida do outro lado'
    ).toBe('cascade');
  });

  it('não repete a chamada quando a pessoa informou o valor', () => {
    const { svc, http } = montar();
    const erro = vi.fn();

    svc.quickInvest({ cash_available: 1000, min_order_value: 50 }).subscribe({ error: erro });

    http
      .expectOne(r => r.url.endsWith('/quick-invest'))
      .flush(RECUSA_DO_NULO, { status: 422, statusText: 'Unprocessable Entity' });

    http.expectNone(r => r.url.endsWith('/surplus'));
    expect(
      erro,
      'um 422 com valor informado é erro de verdade, não versão antiga'
    ).toHaveBeenCalled();
  });

  it('sem sobra para aportar, o erro original sobe em vez de virar zero', () => {
    const { svc, http } = montar();
    const erro = vi.fn();

    svc.quickInvest({ cash_available: null, min_order_value: 50 }).subscribe({ error: erro });

    http
      .expectOne(r => r.url.endsWith('/quick-invest'))
      .flush(RECUSA_DO_NULO, { status: 422, statusText: 'Unprocessable Entity' });

    http.expectOne(r => r.url.endsWith('/surplus')).flush({ cascade: { available_to_invest: 0 } });

    http.expectNone(r => r.url.endsWith('/quick-invest'));
    expect(erro).toHaveBeenCalled();
  });

  it('outro 422 não vira consulta à sobra', () => {
    const { svc, http } = montar();
    const erro = vi.fn();

    svc.quickInvest({ cash_available: null, min_order_value: 50 }).subscribe({ error: erro });

    http
      .expectOne(r => r.url.endsWith('/quick-invest'))
      .flush(
        { detail: [{ loc: ['body', 'min_order_value'], msg: 'nope' }] },
        { status: 422, statusText: 'Unprocessable Entity' }
      );

    http.expectNone(r => r.url.endsWith('/surplus'));
    expect(erro).toHaveBeenCalled();
  });
});
