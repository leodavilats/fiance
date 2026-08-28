import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { OnboardingState, RecommendService } from '../../core';
import { OnboardingComponent } from './onboarding.component';

function estado(over: Partial<OnboardingState> = {}): OnboardingState {
  return {
    step: 2,
    total_steps: 3,
    completed: false,
    onboarded_at: null,
    positions: 0,
    has_goals: false,
    reason: 'Falta registrar a primeira posição.',
    ...over,
  };
}

function setup(options: { passo?: string; estado?: OnboardingState; falha?: boolean } = {}) {
  const completou: boolean[] = [];
  const navegacoes: unknown[] = [];

  const queryParamMap = new Map<string, string>();
  if (options.passo) queryParamMap.set('passo', options.passo);

  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      {
        provide: ActivatedRoute,
        useValue: { snapshot: { queryParamMap } },
      },
      {
        provide: RecommendService,
        useValue: {
          getOnboarding: () =>
            options.falha
              ? throwError(() => new Error('fora do ar'))
              : of(options.estado ?? estado()),
          completeOnboarding: (skipped: boolean) => {
            completou.push(skipped);
            return of(estado({ completed: true }));
          },
        },
      },
    ],
  });

  const router = TestBed.inject(Router);
  vi.spyOn(router, 'navigate').mockImplementation(async (...args: unknown[]) => {
    navegacoes.push(args);
    return true;
  });
  vi.spyOn(router, 'navigateByUrl').mockImplementation(async (url: unknown) => {
    navegacoes.push(url);
    return true;
  });

  const fixture = TestBed.createComponent(OnboardingComponent);
  const component = fixture.componentInstance;
  component.ngOnInit();

  return { component, completou, navegacoes };
}

describe('onboarding', () => {
  beforeEach(() => vi.restoreAllMocks());

  describe('o passo mora na URL', () => {
    it('a URL manda sobre o estado do servidor', () => {
      // Refresh no passo 2 tem que voltar ao passo 2, mesmo que o servidor
      // ache que a pessoa já poderia estar no 3.
      const { component } = setup({ passo: '3', estado: estado({ step: 2 }) });

      expect(component.passoAtual()).toBe(3);
    });

    it('sem passo na URL, entra onde o servidor diz e escreve isso lá', () => {
      const { component, navegacoes } = setup({ estado: estado({ step: 3 }) });

      expect(component.passoAtual()).toBe(3);
      expect(navegacoes.length).toBeGreaterThan(0);
    });

    it('passo fora da faixa cai no estado do servidor em vez de quebrar', () => {
      const { component } = setup({ passo: '99', estado: estado({ step: 2 }) });

      expect(component.passoAtual()).toBe(2);
    });

    it('passo que não é número não vira NaN na tela', () => {
      const { component } = setup({ passo: 'abc', estado: estado({ step: 2 }) });

      expect(component.passoAtual()).toBe(2);
      expect(Number.isNaN(component.progresso())).toBe(false);
    });
  });

  describe('nada bloqueia', () => {
    it('pular conclui e leva para o produto', () => {
      const { component, completou, navegacoes } = setup();

      component.concluir(true);

      expect(completou).toEqual([true]);
      expect(navegacoes).toContain('/hoje');
    });

    it('falha ao carimbar não prende ninguém na tela de boas-vindas', () => {
      const { component, navegacoes } = setup();
      TestBed.inject(RecommendService).completeOnboarding = () =>
        throwError(() => new Error('backend fora do ar'));

      component.concluir(false);

      expect(navegacoes).toContain('/hoje');
    });

    it('o backend fora do ar não deixa a tela sem passo', () => {
      const { component } = setup({ falha: true, passo: '2' });

      expect(component.passoAtual()).toBe(2);
    });
  });

  describe('passo já satisfeito', () => {
    it('quem já tem carteira vê o passo 2 como feito', () => {
      const { component } = setup({ passo: '2', estado: estado({ positions: 3 }) });

      expect(component.passoConcluido()).toBe(true);
    });

    it('quem não tem meta vê o passo 3 como pendente', () => {
      const { component } = setup({ passo: '3', estado: estado({ has_goals: false }) });

      expect(component.passoConcluido()).toBe(false);
    });
  });

  it('o último passo conclui em vez de avançar para o vazio', () => {
    const { component, completou } = setup({ passo: '3' });

    component.proximo();

    expect(completou).toEqual([false]);
  });
});
