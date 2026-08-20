/**
 * Régua única do score de oportunidade (0–100).
 *
 * O mesmo número tinha três réguas: 70 no texto do glossário, 75/60/40 em
 * `scoreLabel()` e 75 em `is_interesting` no backend. Espelha
 * `backend/app/analysis/score_ruler.py` — ao mudar um, mudar os dois (e
 * `mobile/lib/core/score_ruler.dart`).
 */
export const SCORE_STRONG = 75;
export const SCORE_GOOD = 60;
export const SCORE_NEUTRAL = 40;

/** DY mínimo (%) para um score alto ser tratado como destaque de renda. */
export const HIGHLIGHT_MIN_DY = 6;

/**
 * Abaixo disso o score é chute, não medida: a UI apresenta como
 * "dado insuficiente" em vez de colorir a nota. Espelha
 * `scoring.MIN_DATA_COMPLETENESS` no backend.
 */
export const MIN_DATA_COMPLETENESS = 0.5;

export interface ScoreBand {
  text: string;
  cls: string;
}

export function scoreBand(score: number): ScoreBand {
  if (score >= SCORE_STRONG) return { text: 'Excelente entrada', cls: 'text-green-400' };
  if (score >= SCORE_GOOD) return { text: 'Boa oportunidade', cls: 'text-accent' };
  if (score >= SCORE_NEUTRAL) return { text: 'Neutro', cls: 'text-yellow-400' };
  return { text: 'Evitar agora', cls: 'text-red-400' };
}

/** Texto do glossário derivado dos próprios limiares — não pode divergir. */
export const SCORE_GLOSSARY =
  `Pontuação 0–100 calculada pelo sistema combinando margem de segurança (preço justo), ` +
  `dividendos, qualidade e endividamento, ponderados pelo seu perfil de risco. ` +
  `A partir de ${SCORE_STRONG} = excelente entrada; ${SCORE_GOOD}–${SCORE_STRONG - 1} = boa ` +
  `oportunidade; ${SCORE_NEUTRAL}–${SCORE_GOOD - 1} = neutro; abaixo de ${SCORE_NEUTRAL} = ` +
  `evitar agora.`;
