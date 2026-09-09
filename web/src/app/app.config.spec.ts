import { LOCALE_ID } from '@angular/core';
import { describe, expect, it } from 'vitest';
import { appConfig } from './app.config';

describe('idioma da aplicação', () => {
  it('os pipes de número saem em pt-BR, não no default en-US', () => {
    const locale = appConfig.providers.find(
      p => typeof p === 'object' && p !== null && 'provide' in p && p.provide === LOCALE_ID
    );

    expect(
      locale,
      'sem LOCALE_ID o Angular assume en-US: R$ 120,000 é lido como cento e vinte reais por ' +
        'quem usa vírgula como separador decimal'
    ).toBeDefined();
    expect((locale as { useValue: string }).useValue).toBe('pt-BR');
  });

  it('ponto e vírgula trocam de papel entre os dois idiomas', () => {
    expect((120000).toLocaleString('en-US')).toBe('120,000');
    expect((120000).toLocaleString('pt-BR')).toBe('120.000');
  });
});
