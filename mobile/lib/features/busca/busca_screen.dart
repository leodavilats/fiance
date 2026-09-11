import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_state.dart';

class BuscaDestino {
  const BuscaDestino({
    required this.title,
    required this.subtitle,
    required this.route,
    required this.terms,
  });

  final String title;
  final String subtitle;
  final String route;
  final List<String> terms;
}

const buscaDestinos = <BuscaDestino>[
  // Os cinco destinos primeiro, na ordem do ciclo do dinheiro. Os termos antigos continuam
  // buscaveis de proposito: quem procura "hoje" ou "estrategia" tem de achar a casa nova.
  BuscaDestino(
    title: 'Mês',
    subtitle: 'O que aconteceu com seu dinheiro, e o que exige atenção',
    route: '/mes',
    terms: [
      'mes',
      'hoje',
      'caixa',
      'lancar',
      'lancamento',
      'gasto',
      'salario',
      'conta',
      'vencer',
      'resumo',
      'inicio',
    ],
  ),
  BuscaDestino(
    title: 'Sobra',
    subtitle: 'O que fazer com o que ficou, na ordem que a sobra pede',
    route: '/sobra',
    terms: [
      'sobra',
      'sobrou',
      'estrategia',
      'ordem',
      'cascata',
      'divida',
      'reserva',
      'livre',
    ],
  ),
  BuscaDestino(
    title: 'O que aconteceu',
    subtitle: 'Histórico de mudanças, metas e proventos',
    route: '/mes/atividade',
    terms: ['atividade', 'historico', 'aconteceu', 'mudancas'],
  ),
  BuscaDestino(
    title: 'Patrimônio',
    subtitle: 'Posições, composição e proventos',
    route: '/patrimonio',
    terms: [
      'carteira',
      'posicoes',
      'composicao',
      'provento',
      'dividendo',
      'jcp',
    ],
  ),
  BuscaDestino(
    title: 'Objetivos',
    subtitle: 'A alocação-alvo por categoria e setor',
    route: '/voce/objetivos',
    terms: ['meta', 'metas', 'alocacao', 'objetivo', 'alvo'],
  ),
  BuscaDestino(
    title: 'Onde aportar',
    subtitle: 'Distribuir um aporte pelo que está longe da meta',
    route: '/sobra/aporte',
    terms: ['aporte', 'aportar', 'investir', 'comprar'],
  ),
  BuscaDestino(
    title: 'Renda fixa',
    subtitle: 'Comparar títulos depois do IR',
    route: '/descobrir/renda-fixa',
    terms: ['renda fixa', 'cdb', 'lci', 'lca', 'tesouro', 'selic', 'cdi'],
  ),
  BuscaDestino(
    title: 'Renda fixa × bolsa',
    subtitle: 'Renda contratada contra dividendo de bolsa',
    route: '/descobrir/renda-fixa-vs-bolsa',
    terms: ['renda fixa x bolsa', 'cdb ou fii', 'comparar renda'],
  ),
  BuscaDestino(
    title: 'Projeção de renda passiva',
    subtitle: 'Aportando assim, onde eu chego',
    route: '/patrimonio/projecao',
    terms: ['projecao', 'projetar', 'renda passiva', 'futuro'],
  ),
  BuscaDestino(
    title: 'Quedas',
    subtitle: 'O que caiu e por quê',
    route: '/descobrir/quedas',
    terms: ['queda', 'quedas', 'caiu', 'desabou'],
  ),
  BuscaDestino(
    title: 'Você',
    subtitle: 'Conta, alertas, indicação e preferências',
    route: '/voce',
    terms: [
      'conta',
      'configuracao',
      'alerta',
      'indicacao',
      'exportar',
      'excluir',
      'tema',
    ],
  ),
];

String dobrar(String texto) {
  const comAcento = 'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ';
  const semAcento = 'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC';
  final buffer = StringBuffer();
  for (final char in texto.toLowerCase().runes) {
    final atual = String.fromCharCode(char);
    final indice = comAcento.indexOf(atual);
    buffer.write(indice >= 0 ? semAcento[indice].toLowerCase() : atual);
  }
  return buffer.toString();
}

List<BuscaDestino> destinosPara(String query) {
  final termo = dobrar(query.trim());
  if (termo.isEmpty) return const [];
  return buscaDestinos
      .where(
        (d) =>
            dobrar(d.title).contains(termo) ||
            d.terms.any((t) => dobrar(t).contains(termo)),
      )
      .take(5)
      .toList();
}

String rotaDoAchado(SearchHit hit) =>
    hit.kind == 'fixed_income' ? '/patrimonio/renda-fixa' : '/ativo/${hit.ref}';

class BuscaScreen extends ConsumerStatefulWidget {
  const BuscaScreen({super.key});

  @override
  ConsumerState<BuscaScreen> createState() => _BuscaScreenState();
}

class _BuscaScreenState extends ConsumerState<BuscaScreen> {
  final _ctrl = TextEditingController();
  Timer? _debounce;

  SearchResults? _results;
  Object? _error;
  String _query = '';

  @override
  void dispose() {
    _debounce?.cancel();
    _ctrl.dispose();
    super.dispose();
  }

  void _onChanged(String value) {
    setState(() => _query = value);
    _debounce?.cancel();

    if (value.trim().length < 2) {
      setState(() {
        _results = null;
        _error = null;
      });
      return;
    }

    _debounce = Timer(const Duration(milliseconds: 250), () async {
      try {
        final res = await ref.read(apiRepositoryProvider).search(value.trim());
        if (mounted) {
          setState(() {
            _results = res;
            _error = null;
          });
        }
      } catch (err) {
        if (mounted) {
          setState(() {
            _results = null;
            _error = err;
          });
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final ink3 = isDark ? FiColors.darkInk3 : FiColors.lightInk3;
    final destinos = destinosPara(_query);
    final grupos = _results?.groups ?? const <SearchGroup>[];

    return Scaffold(
      appBar: AppBar(
        title: TextField(
          controller: _ctrl,
          autofocus: true,
          onChanged: _onChanged,
          decoration: const InputDecoration(
            hintText: 'Buscar ativo, título ou tela',
            border: InputBorder.none,
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          FiLayout.scrollTail,
        ),
        children: [
          for (final grupo in grupos) ...[
            _Cabecalho(texto: grupo.label, cor: ink3),
            FiRows(
              children: [
                for (final hit in grupo.items)
                  FiDataRow(
                    label: hit.title,
                    detail: hit.subtitle,
                    onTap: () => context.go(rotaDoAchado(hit)),
                  ),
              ],
            ),
          ],

          if (destinos.isNotEmpty) ...[
            _Cabecalho(texto: 'Ir para', cor: ink3),
            FiRows(
              children: [
                for (final d in destinos)
                  FiDataRow(
                    label: d.title,
                    detail: d.subtitle,
                    onTap: () => context.go(d.route),
                  ),
              ],
            ),
          ],

          if (_error != null && destinos.isEmpty)
            Padding(
              padding: const EdgeInsets.only(top: FiSpace.s4),
              child: FiErrorState(error: _error!, action: 'buscar'),
            ),

          if (_query.trim().length >= 2 &&
              grupos.isEmpty &&
              destinos.isEmpty &&
              _error == null)
            FiEmptyState(
              title: 'Nada encontrado para "${_query.trim()}"',
              body: 'A busca cobre a sua carteira, sua renda fixa, o universo de ativos da B3 '
                  'e as telas do produto. Um ticker inteiro costuma achar mais que um pedaço.',
            ),
        ],
      ),
    );
  }
}

class _Cabecalho extends StatelessWidget {
  const _Cabecalho({required this.texto, required this.cor});

  final String texto;
  final Color cor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: FiSpace.s5, bottom: FiSpace.s2),
      child: Text(
        texto.toUpperCase(),
        style: FiType.eyebrow.copyWith(color: cor),
      ),
    );
  }
}
