import { fiBandFor, fiHealthBands } from './score-ruler';

export const MIN_POSICOES_PARA_SAUDE = 4;

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
