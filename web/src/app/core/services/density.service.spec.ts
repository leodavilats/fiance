import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { beforeEach, describe, expect, it } from 'vitest';
import { DensityService } from './density.service';
import { RecommendService } from './recommend.service';

function setup(options: { density?: string; falha?: boolean } = {}) {
  const salvos: unknown[] = [];

  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [
      {
        provide: RecommendService,
        useValue: {
          getPreferences: () =>
            options.falha
              ? throwError(() => new Error('fora do ar'))
              : of({ density: options.density }),
          savePreferences: (patch: unknown) => {
            salvos.push(patch);
            return of({});
          },
        },
      },
    ],
  });

  return { service: TestBed.inject(DensityService), salvos };
}

describe('densidade', () => {
  beforeEach(() => {
    delete document.documentElement.dataset['density'];
  });

  it('a preferência da conta chega ao documento', () => {
    // O CSS já sabe reagir a [data-density]; o que faltava era escrever o
    // atributo a partir de uma fonte que faça sentido.
    const { service } = setup({ density: 'compact' });

    service.ensureLoaded();

    expect(service.density()).toBe('compact');
    expect(document.documentElement.dataset['density']).toBe('compact');
  });

  it('sem preferência guardada, usa o confortável', () => {
    const { service } = setup({ density: undefined });

    service.ensureLoaded();

    expect(service.density()).toBe('comfortable');
  });

  it('backend fora do ar não deixa a tela sem densidade', () => {
    // Densidade errada é uma tela mais larga do que a pessoa queria; derrubar
    // a navegação por isso seria desproporcional.
    const { service } = setup({ falha: true });

    service.ensureLoaded();

    expect(service.density()).toBe('comfortable');
    expect(document.documentElement.dataset['density']).toBe('comfortable');
  });

  it('a preferência é buscada uma vez por sessão', () => {
    let chamadas = 0;
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        {
          provide: RecommendService,
          useValue: {
            getPreferences: () => {
              chamadas += 1;
              return of({ density: 'compact' });
            },
            savePreferences: () => of({}),
          },
        },
      ],
    });
    const service = TestBed.inject(DensityService);

    service.ensureLoaded();
    service.ensureLoaded();
    service.ensureLoaded();

    expect(chamadas).toBe(1);
  });

  it('trocar aplica na hora e persiste na conta', () => {
    const { service, salvos } = setup({ density: 'comfortable' });
    service.ensureLoaded();

    service.set('compact');

    expect(document.documentElement.dataset['density']).toBe('compact');
    expect(salvos).toEqual([{ density: 'compact' }]);
  });

  it('falha ao persistir não desfaz o que a pessoa já vê', () => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        {
          provide: RecommendService,
          useValue: {
            getPreferences: () => of({ density: 'comfortable' }),
            savePreferences: () => throwError(() => new Error('fora do ar')),
          },
        },
      ],
    });
    const service = TestBed.inject(DensityService);

    service.set('compact');

    expect(service.density()).toBe('compact');
  });
});
