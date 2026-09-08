/// O mes como recorte, espelhando `web/src/app/core/mes.ts`.
///
/// Mesmo conceito e mesmo nome nas duas plataformas, implementacao de cada uma -- e por isso
/// aqui nao ha `Intl`: seriam duas fontes para o nome do mes, e o web escreve a lista a mao.
const _nomes = [
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

/// `2026-09` -> `setembro de 2026`.
String nomeDoMes(String mes) {
  final partes = mes.split('-');
  if (partes.length < 2) return mes;
  final m = int.tryParse(partes[1]);
  final nome = (m != null && m >= 1 && m <= 12) ? _nomes[m - 1] : mes;
  return '$nome de ${partes[0]}';
}

/// O mes corrente do relogio local, no formato `YYYY-MM`.
String mesCorrente() {
  final agora = DateTime.now();
  return '${agora.year}-${agora.month.toString().padLeft(2, '0')}';
}

/// O mes anterior a `mes`, no mesmo formato.
String mesAnterior(String mes) {
  final partes = mes.split('-');
  final ano = int.tryParse(partes.first) ?? DateTime.now().year;
  final m = partes.length > 1 ? (int.tryParse(partes[1]) ?? 1) : 1;
  return m == 1
      ? '${ano - 1}-12'
      : '$ano-${(m - 1).toString().padLeft(2, '0')}';
}

/// O dia do mes, de uma data `YYYY-MM-DD`. Serve para a coluna de dia da linha do tempo.
String diaDe(String data) => data.length >= 10 ? data.substring(8, 10) : data;
