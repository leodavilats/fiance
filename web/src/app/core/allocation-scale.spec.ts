import { describe, expect, it } from 'vitest';
import { allocationScalePct } from './ruler';

const linha = (currentPct: number, targetPct: number | null) => ({ currentPct, targetPct });

describe('escala compartilhada das barras de meta', () => {
  it('tira a lista do canto esquerdo quando as metas são pequenas', () => {
    const escala = allocationScalePct([linha(12, 20), linha(8, 15)]);

    expect(escala).toBeLessThan(100);
    expect(20 / escala).toBeGreaterThan(0.5);
  });

  it('usa a mesma régua para todas as linhas, então elas se comparam', () => {
    const escala = allocationScalePct([linha(40, 50), linha(5, 10)]);

    expect(escala).toBeGreaterThanOrEqual(50);
  });

  it('acomoda o maior valor, venha do atual ou da meta', () => {
    expect(allocationScalePct([linha(80, 20)])).toBeGreaterThanOrEqual(80);
    expect(allocationScalePct([linha(20, 80)])).toBeGreaterThanOrEqual(80);
  });

  it('não passa de 100% nem colapsa numa carteira vazia', () => {
    expect(allocationScalePct([linha(95, 100)])).toBeLessThanOrEqual(100);
    expect(allocationScalePct([])).toBe(100);
    expect(allocationScalePct([linha(0, 0)])).toBe(100);
  });

  it('categoria sem meta não puxa a escala', () => {
    expect(allocationScalePct([linha(10, null)])).toBeGreaterThanOrEqual(10);
  });

  it('meta minúscula ainda tem régua legível', () => {
    expect(allocationScalePct([linha(1, 2)])).toBeGreaterThanOrEqual(10);
  });
});
