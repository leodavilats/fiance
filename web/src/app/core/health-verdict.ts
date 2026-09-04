import { fiBandFor, fiHealthBands } from './score-ruler';

/**
 * Abaixo disto, concentração e diversificação não dizem nada.
 *
 * Vivia duplicado em `dashboard.component.ts` e `carteira-resumo.component.ts`
 * como duas constantes locais de mesmo valor.
 */
export const MIN_POSICOES_PARA_SAUDE = 4;

/**
 * A frase que o sistema usa para descrever a saúde da carteira.
 *
 * Existe uma só, e é a mesma em Hoje e na Carteira. Antes, Hoje dizia
 * "Carteira saudável" em serifa e a Carteira mostrava a mesma pontuação como
 * um eyebrow e uma régua, sem frase nenhuma — o mesmo objeto, duas gramáticas,
 * e nada dizia à pessoa que era a mesma leitura.
 *
 * Não recebe o score cru: recebe também quantas posições sustentam a conta,
 * porque "não temos base para avaliar" é um veredito legítimo e precisa sair
 * daqui, não de um `@if` em cada tela.
 */
export function vereditoDeSaude(score: number, posicoes: number): string {
  if (posicoes < MIN_POSICOES_PARA_SAUDE) {
    return 'Sua carteira ainda é pequena para uma leitura de risco';
  }

  switch (fiBandFor(score, fiHealthBands).id) {
    case 'healthy':
      return 'Carteira saudável';
    case 'ok':
      return 'Carteira em ordem, com pontos de atenção';
    case 'watch':
      return 'Sua carteira merece atenção';
    default:
      return 'Sua carteira precisa de ajustes';
  }
}

/**
 * Por que o veredito é esse — no máximo três razões, a mais pesada primeiro.
 *
 * Recebe o que o backend já apurou; não classifica nada por conta própria.
 */
export function razoesDaSaude(entrada: {
  readonly posicoes: number;
  readonly topPositionTicker: string | null;
  readonly topPositionPct: number | null;
  readonly topSectorLabel: string | null;
  readonly topSectorPct: number | null;
  readonly warnings: readonly string[];
}): string[] {
  if (entrada.posicoes < MIN_POSICOES_PARA_SAUDE) {
    const plural = entrada.posicoes === 1 ? 'ativo' : 'ativos';
    return [
      `Com ${entrada.posicoes} ${plural}, concentração e diversificação ainda não dizem muito.`,
    ];
  }

  const razoes: string[] = [];

  if (entrada.topPositionTicker && entrada.topPositionPct != null && entrada.topPositionPct >= 15) {
    razoes.push(
      `${entrada.topPositionTicker} concentra ${entrada.topPositionPct.toFixed(1)}% da carteira.`
    );
  }
  if (entrada.topSectorLabel && entrada.topSectorPct != null && entrada.topSectorPct >= 40) {
    razoes.push(
      `${entrada.topSectorLabel} responde por ${entrada.topSectorPct.toFixed(1)}% das ações e BDRs.`
    );
  }

  for (const aviso of entrada.warnings) {
    if (razoes.length >= 3) break;
    if (!razoes.includes(aviso)) razoes.push(aviso);
  }

  if (razoes.length === 0) {
    razoes.push('Nenhum ponto de concentração ou risco relevante identificado.');
  }
  return razoes.slice(0, 3);
}
