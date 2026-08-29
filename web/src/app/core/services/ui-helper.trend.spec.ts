import { describe, expect, it } from 'vitest';
import { UiHelperService } from './ui-helper.service';

/**
 * O rótulo precisa casar com `trendLabel` do mobile
 * (`mobile/lib/core/labels.dart`). Foi a divergência entre os dois — o web
 * traduzindo e o mobile mostrando o valor cru — que pôs `unknown` na tela.
 */
describe('rótulo de tendência', () => {
  const ui = new UiHelperService();

  it('as três direções têm nome em português', () => {
    expect(ui.trendLabel('uptrend')).toBe('↗ Alta');
    expect(ui.trendLabel('downtrend')).toBe('↘ Baixa');
    expect(ui.trendLabel('sideways')).toBe('→ Lateral');
  });

  it('sem histórico não vira uma quarta direção', () => {
    expect(ui.trendLabel('unknown')).toBe('sem histórico suficiente');
    expect(ui.trendLabel('')).toBe('sem histórico suficiente');
  });

  it('nenhum valor cru do backend vaza para a tela', () => {
    for (const cru of ['uptrend', 'downtrend', 'sideways', 'unknown']) {
      expect(ui.trendLabel(cru)).not.toContain(cru);
    }
  });
});
