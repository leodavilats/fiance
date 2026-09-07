import { describe, expect, it } from 'vitest';
import { MIN_POSICOES_PARA_SAUDE, razoesDaSaude, vereditoDeSaude } from './health-verdict';

/*
 * Estes casos moravam em `dashboard.component.spec.ts`, e vieram junto quando `/hoje` se
 * dissolveu. Testar as funções direto é melhor do que estava: elas são puras, e o veredito de
 * saúde continua vivo em `/patrimonio` — apagá-los com a tela teria sido perda de cobertura de
 * uma lógica que não saiu do produto.
 */

function razoes(over: Partial<Parameters<typeof razoesDaSaude>[0]> = {}): string[] {
  return razoesDaSaude({
    posicoes: 6,
    topPositionTicker: null,
    topPositionPct: null,
    topSectorLabel: null,
    topSectorPct: null,
    warnings: [],
    ...over,
  });
}

describe('veredito de saúde da carteira', () => {
  it('carteira pequena não recebe veredito, recebe a razão de não ter', () => {
    expect(vereditoDeSaude(80, 3)).toContain('pequena');
    expect(razoes({ posicoes: 3 })[0]).toContain('3 ativos');
  });

  it('o singular do motivo acompanha a contagem', () => {
    expect(razoes({ posicoes: 1 })[0]).toContain('1 ativo,');
  });

  it('a partir de quatro ativos o veredito vem da faixa da régua', () => {
    expect(vereditoDeSaude(80, MIN_POSICOES_PARA_SAUDE)).toBe('Carteira saudável');
    expect(vereditoDeSaude(10, MIN_POSICOES_PARA_SAUDE)).not.toBe('Carteira saudável');
  });

  it('concentração vira motivo apenas acima do limiar que a torna relevante', () => {
    const abaixo = razoes({ topPositionTicker: 'PETR4', topPositionPct: 14.9 });
    const acima = razoes({ topPositionTicker: 'PETR4', topPositionPct: 15 });

    expect(abaixo.some(r => r.includes('PETR4'))).toBe(false);
    expect(acima.some(r => r.includes('PETR4'))).toBe(true);
  });

  it('carteira sem ponto de risco diz isso, em vez de ficar em branco', () => {
    const r = razoes();

    expect(r).toHaveLength(1);
    expect(r[0]).toContain('Nenhum ponto');
  });

  it('no máximo três motivos, para o veredito continuar legível', () => {
    const r = razoes({
      topPositionTicker: 'PETR4',
      topPositionPct: 30,
      topSectorLabel: 'Bancos',
      topSectorPct: 55,
      warnings: ['a', 'b', 'c', 'd'],
    });

    expect(r.length).toBeLessThanOrEqual(3);
  });
});
