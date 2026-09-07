const NOMES = [
  'janeiro',
  'fevereiro',
  'março',
  'abril',
  'maio',
  'junho',
  'julho',
  'agosto',
  'setembro',
  'outubro',
  'novembro',
  'dezembro',
];

/** `2026-09` → `setembro de 2026`. */
export function nomeDoMes(mes: string): string {
  const [ano, m] = mes.split('-');
  return `${NOMES[Number(m) - 1] ?? mes} de ${ano}`;
}

/** O mês corrente do relógio local, no formato `YYYY-MM`. */
export function mesCorrente(): string {
  const agora = new Date();
  return `${agora.getFullYear()}-${String(agora.getMonth() + 1).padStart(2, '0')}`;
}
