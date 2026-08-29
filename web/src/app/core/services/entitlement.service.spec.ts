import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { beforeEach, describe, expect, it } from 'vitest';
import { EntitlementService } from './entitlement.service';

function comEstado(estado: Record<string, unknown>) {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [provideHttpClient(), provideHttpClientTesting()],
  });
  const service = TestBed.inject(EntitlementService);
  const http = TestBed.inject(HttpTestingController);
  service.ensureLoaded();
  http.expectOne(req => req.url.endsWith('/entitlements')).flush(estado);
  return service;
}

const PREMIUM_EM_TRIAL = {
  plan: 'premium',
  unrestricted: false,
  in_trial: true,
  features: {},
  limits: {},
};

describe('direitos', () => {
  beforeEach(() => TestBed.resetTestingModule());

  describe('enquanto a resposta não chega', () => {
    it('o produto se comporta como se tudo fosse permitido', () => {
      TestBed.configureTestingModule({
        providers: [provideHttpClient(), provideHttpClientTesting()],
      });
      const service = TestBed.inject(EntitlementService);

      expect(service.unrestricted()).toBe(true);
    });
  });

  describe('contador de teste', () => {
    it('conta os dias que faltam', () => {
      const service = comEstado({ ...PREMIUM_EM_TRIAL, trial_days_left: 9 });

      expect(service.inTrial()).toBe(true);
      expect(service.trialDaysLeft()).toBe(9);
    });

    it('não avisa no meio do teste', () => {
      const service = comEstado({ ...PREMIUM_EM_TRIAL, trial_days_left: 9 });

      expect(service.trialEndingSoon()).toBe(false);
    });

    it('avisa a partir de D-3', () => {
      const service = comEstado({ ...PREMIUM_EM_TRIAL, trial_days_left: 3 });

      expect(service.trialEndingSoon()).toBe(true);
    });

    it('avisa em D-1', () => {
      const service = comEstado({ ...PREMIUM_EM_TRIAL, trial_days_left: 1 });

      expect(service.trialEndingSoon()).toBe(true);
    });

    it('avisa no último dia', () => {
      const service = comEstado({ ...PREMIUM_EM_TRIAL, trial_days_left: 0 });

      expect(service.trialEndingSoon()).toBe(true);
    });

    it('quem não está em teste não vê contador', () => {
      const service = comEstado({
        plan: 'free',
        unrestricted: false,
        in_trial: false,
        trial_days_left: null,
        features: {},
        limits: {},
      });

      expect(service.inTrial()).toBe(false);
      expect(service.trialDaysLeft()).toBeNull();
      expect(service.trialEndingSoon()).toBe(false);
    });

    it('a contagem vem do servidor, não do relógio do navegador', () => {
      const service = comEstado({ ...PREMIUM_EM_TRIAL, trial_days_left: 2, trial_ends_at: 0 });

      expect(service.trialDaysLeft()).toBe(2);
    });
  });
});
