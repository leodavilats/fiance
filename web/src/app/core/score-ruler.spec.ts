import { describe, expect, it } from 'vitest';
import {
  MIN_DATA_COMPLETENESS,
  SCORE_GLOSSARY,
  SCORE_GOOD,
  SCORE_NEUTRAL,
  SCORE_STRONG,
  dataCompletenessLabel,
  fiScoreBands,
  fiScoreIsReliable,
  scoreBand,
  scoreBandFor,
  stateTextClass,
} from './score-ruler';

describe('régua de score', () => {
  it('as faixas cobrem 0 a 100 sem buraco nem sobreposição', () => {
    const bands = fiScoreBands.filter(b => b.min !== null).sort((a, b) => a.min! - b.min!);

    expect(bands[0].min).toBe(0);
    expect(bands[bands.length - 1].max).toBe(100);

    for (let i = 1; i < bands.length; i++) {
      expect(bands[i].min).toBe(bands[i - 1].max! + 1);
    }
  });

  it('cada limiar cai na faixa que o nomeia', () => {
    expect(scoreBand(SCORE_STRONG).text).toBe(scoreBand(100).text);
    expect(scoreBand(SCORE_STRONG - 1).text).not.toBe(scoreBand(SCORE_STRONG).text);
    expect(scoreBand(SCORE_GOOD).text).not.toBe(scoreBand(SCORE_GOOD - 1).text);
    expect(scoreBand(SCORE_NEUTRAL).text).not.toBe(scoreBand(SCORE_NEUTRAL - 1).text);
  });

  it('dado incompleto derruba a ênfase em vez de mentir um veredito', () => {
    const completo = scoreBandFor(90, 1);
    const incompleto = scoreBandFor(90, MIN_DATA_COMPLETENESS - 0.2);

    expect(completo.emphasis).toBe('strong');
    expect(incompleto.emphasis).toBe('muted');
    expect(fiScoreIsReliable(MIN_DATA_COMPLETENESS - 0.2)).toBe(false);
    expect(fiScoreIsReliable(1)).toBe(true);
  });

  it('o rótulo de completude só aparece quando falta indicador', () => {
    expect(dataCompletenessLabel(1)).toBe('');
    expect(dataCompletenessLabel(null)).toBe('');
    expect(dataCompletenessLabel(0.6)).toBe('60% dos indicadores disponíveis');
  });

  it('estado vira classe de papel, nunca cor crua do Tailwind', () => {
    const classes = (
      ['favorable', 'attention', 'adverse', 'indeterminate', 'neutral'] as const
    ).map(stateTextClass);

    for (const cls of classes) {
      expect(cls.startsWith('text-')).toBe(true);
      expect(cls).not.toMatch(/text-(red|green|yellow|gray|grey|white|black)/);
    }
  });

  it('o glossário cita os mesmos limiares da régua, não números escritos à mão', () => {
    for (const band of fiScoreBands.filter(b => b.min !== null)) {
      expect(SCORE_GLOSSARY).toContain(String(band.min));
      expect(SCORE_GLOSSARY.toLowerCase()).toContain(band.label.toLowerCase());
    }
    expect(SCORE_GLOSSARY).toContain('não recomendação');
  });
});
