import { describe, expect, it } from 'vitest';
import { environment as desenvolvimento } from './environment.development';
import { environment as e2e } from './environment.e2e';
import { environment as publicado } from './environment';

describe('ambientes', () => {
  describe('o publicado', () => {
    it('não aponta para a máquina de ninguém', () => {
      expect(publicado.apiBaseUrl).not.toMatch(/localhost|127\.0\.0\.1|0\.0\.0\.0/);
    });

    it('fala HTTPS', () => {
      expect(publicado.apiBaseUrl.startsWith('https://')).toBe(true);
    });

    it('está marcado como produção', () => {
      expect(publicado.production).toBe(true);
    });
  });

  describe('todos', () => {
    const ambientes = [
      ['publicado', publicado],
      ['desenvolvimento', desenvolvimento],
      ['e2e', e2e],
    ] as const;

    for (const [nome, ambiente] of ambientes) {
      it(`${nome} inclui o prefixo /api`, () => {
        expect(ambiente.apiBaseUrl.endsWith('/api')).toBe(true);
      });

      it(`${nome} não termina em barra`, () => {
        expect(ambiente.apiBaseUrl.endsWith('/')).toBe(false);
      });
    }
  });

  describe('os locais', () => {
    it('não se dizem produção', () => {
      expect(desenvolvimento.production).toBe(false);
      expect(e2e.production).toBe(false);
    });

    it('apontam para a própria máquina', () => {
      expect(desenvolvimento.apiBaseUrl).toMatch(/localhost|127\.0\.0\.1/);
      expect(e2e.apiBaseUrl).toMatch(/localhost|127\.0\.0\.1/);
    });
  });
});
