/// O mes como recorte.
///
/// A lista de nomes e escrita a mao de proposito: com `Intl` o nome do mes teria duas fontes,
/// uma delas dependente de locale carregado.
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
