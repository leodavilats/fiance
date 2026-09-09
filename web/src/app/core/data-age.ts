/**
 * A idade de um dado externo, em uma frase — "agora", "há 4 min", ou a data quando não é de hoje.
 *
 * Um preço de anteontem muda a decisão, então o momento acompanha o número que ele qualifica.
 * O carimbo é o `as_of` do coletor, em **segundos** epoch, e é o mesmo em toda plataforma.
 */
export function idadeDoDado(carimbo: number | null | undefined, agora = Date.now()): string {
  if (!carimbo) return '';

  const minutos = Math.floor((agora / 1000 - carimbo) / 60);
  if (minutos < 1) return 'agora';
  if (minutos < 60) return `há ${minutos} min`;
  if (minutos < 60 * 24) return `há ${Math.floor(minutos / 60)} h`;
  return `em ${new Date(carimbo * 1000).toLocaleDateString('pt-BR')}`;
}

const UM_DIA_EM_MINUTOS = 60 * 24;

/** Dado de outro dia é o que a pessoa precisa notar; minuto e hora são rotina. */
export function dadoEnvelhecido(carimbo: number | null | undefined, agora = Date.now()): boolean {
  if (!carimbo) return false;
  return (agora / 1000 - carimbo) / 60 >= UM_DIA_EM_MINUTOS;
}

/**
 * O carimbo que representa um conjunto: o **mais antigo**.
 *
 * Numa tabela de trinta preços, dizer a idade do mais novo é prometer frescor que a linha de
 * baixo não tem. É o mesmo critério de `opportunity_service.market_data_age_seconds`.
 */
export function carimboMaisAntigo(carimbos: readonly (number | null | undefined)[]): number | null {
  const validos = carimbos.filter((c): c is number => typeof c === 'number' && c > 0);
  return validos.length ? Math.min(...validos) : null;
}
