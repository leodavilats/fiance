import { fiBandFor, fiMonthPressureBands, type FiScoreBand } from './score-ruler';

export interface VereditoDoMes {
  readonly band: FiScoreBand;

  /** Quanto do que entrou já está comprometido, em %. `null` quando não há o que dividir. */
  readonly pressao: number | null;

  readonly veredito: string;
  readonly razao: string;
}

/**
 * A leitura do mês, na régua de `monthPressureRuler`.
 *
 * Sem entrada lançada não há razão a calcular, e a banda é a de leitura ausente — dividir por
 * zero daria 0% e "Mês folgado" para quem não lançou nada.
 *
 * Dívida caseira não muda a banda: a régua mede pressão do mês, e `class === 'expensive'` já é
 * julgamento do backend sobre outra coisa. O que ela faz é assumir a razão, porque um mês
 * folgado com dívida a 14,9% ao mês não é um mês resolvido.
 */
export function vereditoDoMes(entrada: {
  readonly recebido: number;
  readonly comprometido: number;
  readonly dividaCara: {
    readonly description: string;
    readonly monthly_rate: number | null;
  } | null;
}): VereditoDoMes {
  const { recebido, comprometido, dividaCara } = entrada;

  if (recebido <= 0) {
    return {
      band: fiBandFor(0, fiMonthPressureBands, 0),
      pressao: null,
      veredito: 'Ainda não há entrada lançada neste mês',
      razao: 'Sem o que entrou não há como medir o que está comprometido.',
    };
  }

  const pressao = Math.min(100, Math.round((comprometido / recebido) * 100));
  const band = fiBandFor(pressao, fiMonthPressureBands);

  if (dividaCara) {
    const taxa =
      dividaCara.monthly_rate === null
        ? ''
        : ` a ${dividaCara.monthly_rate.toLocaleString('pt-BR', { maximumFractionDigits: 2 })}% ao mês`;
    return {
      band,
      pressao,
      veredito: band.label,
      razao: `O comprometido consome ${pressao}% do que entrou, e ${dividaCara.description}${taxa} come a sobra antes de qualquer aporte.`,
    };
  }

  return {
    band,
    pressao,
    veredito: band.label,
    razao: `O comprometido consome ${pressao}% do que entrou.`,
  };
}
