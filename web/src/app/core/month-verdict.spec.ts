import { describe, expect, it } from 'vitest';
import { vereditoDoMes } from './month-verdict';

function leitura(over: Partial<Parameters<typeof vereditoDoMes>[0]> = {}) {
  return vereditoDoMes({ recebido: 10000, comprometido: 3000, dividaCara: null, ...over });
}

describe('veredito do mês', () => {
  it('sem entrada lançada não há leitura, e a pressão não vira zero', () => {
    const v = leitura({ recebido: 0, comprometido: 500 });
    expect(v.pressao, 'dividir por zero daria 0% e "Mês folgado" para quem não lançou nada').toBe(
      null
    );
    expect(v.band.state, 'ausência de base é estado indeterminado, não favorável').toBe(
      'indeterminate'
    );
  });

  it('a banda sai da régua gerada, e o pior estado é o mês apertado', () => {
    expect(leitura({ comprometido: 9000 }).band.id, '90% comprometido é a faixa apertada').toBe(
      'tight'
    );
    expect(leitura({ comprometido: 7000 }).band.id).toBe('pressured');
    expect(leitura({ comprometido: 4000 }).band.id).toBe('steady');
    expect(leitura({ comprometido: 1000 }).band.id).toBe('loose');
  });

  it('comprometido acima da renda não estoura a régua', () => {
    const v = leitura({ recebido: 1000, comprometido: 4000 });
    expect(v.pressao, 'o domínio para em 100: uma barra que estoura não informa').toBe(100);
    expect(v.band.id).toBe('tight');
  });

  it('dívida caseira assume a razão sem mudar a banda', () => {
    const semDivida = leitura({ comprometido: 1000 });
    const comDivida = leitura({
      comprometido: 1000,
      dividaCara: { description: 'Rotativo do cartão', monthly_rate: 14.9 },
    });

    expect(comDivida.band.id, 'a régua mede pressão do mês, e a dívida é outro julgamento').toBe(
      semDivida.band.id
    );
    expect(
      comDivida.razao,
      'um mês folgado com dívida a 14,9% ao mês não é um mês resolvido'
    ).toContain('Rotativo do cartão');
    expect(comDivida.razao).toContain('14,9% ao mês');
  });

  it('dívida sem taxa informada não inventa taxa na frase', () => {
    const v = leitura({ dividaCara: { description: 'Consignado', monthly_rate: null } });
    expect(v.razao).toContain('Consignado');
    expect(v.razao, 'o produto não estima taxa que a pessoa não informou').not.toContain('%  ao');
    expect(v.razao).not.toMatch(/a null/);
  });
});
