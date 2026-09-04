import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/design_tokens.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';

class BuscaDestino {
  const BuscaDestino({
    required this.title,
    required this.subtitle,
    required this.route,
    required this.icon,
    required this.terms,
  });

  final String title;
  final String subtitle;
  final String route;
  final IconData icon;
  final List<String> terms;
}

const buscaDestinos = <BuscaDestino>[
  BuscaDestino(
    title: 'Hoje',
    subtitle: 'O que mudou desde a última visita',
    route: '/hoje',
    icon: Icons.wb_sunny_outlined,
    terms: ['hoje', 'resumo', 'inicio', 'novidades'],
  ),
  BuscaDestino(
    title: 'O que aconteceu',
    subtitle: 'Histórico de mudanças, metas e proventos',
    route: '/hoje/atividade',
    icon: Icons.history,
    terms: ['atividade', 'historico', 'aconteceu', 'mudancas'],
  ),
  BuscaDestino(
    title: 'Carteira',
    subtitle: 'Posições, composição e proventos',
    route: '/carteira',
    icon: Icons.pie_chart_outline,
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
    title: 'Minhas metas',
    subtitle: 'A alocação-alvo por categoria e setor',
    route: '/estrategia/metas',
    icon: Icons.flag_outlined,
    terms: ['meta', 'metas', 'alocacao', 'objetivo', 'alvo'],
  ),
  BuscaDestino(
    title: 'Onde aportar',
    subtitle: 'Distribuir um aporte pelo que está longe da meta',
    route: '/estrategia/aporte',
    icon: Icons.add_circle_outline,
    terms: ['aporte', 'aportar', 'investir', 'comprar'],
  ),
  BuscaDestino(
    title: 'Renda fixa',
    subtitle: 'Comparar títulos depois do IR',
    route: '/estrategia/renda-fixa',
    icon: Icons.account_balance_outlined,
    terms: ['renda fixa', 'cdb', 'lci', 'lca', 'tesouro', 'selic', 'cdi'],
  ),
  BuscaDestino(
    title: 'Renda fixa × bolsa',
    subtitle: 'Renda contratada contra dividendo de bolsa',
    route: '/estrategia/renda-fixa-vs-bolsa',
    icon: Icons.compare_arrows_outlined,
    terms: ['renda fixa x bolsa', 'cdb ou fii', 'comparar renda'],
  ),
  BuscaDestino(
    title: 'Projeção de renda passiva',
    subtitle: 'Aportando assim, onde eu chego',
    route: '/estrategia/projecao',
    icon: Icons.timeline_outlined,
    terms: ['projecao', 'projetar', 'renda passiva', 'futuro'],
  ),
  BuscaDestino(
    title: 'Quedas',
    subtitle: 'O que caiu e por quê',
    route: '/descobrir/quedas',
    icon: Icons.trending_down,
    terms: ['queda', 'quedas', 'caiu', 'desabou'],
  ),
  BuscaDestino(
    title: 'Você',
    subtitle: 'Conta, alertas, indicação e preferências',
    route: '/voce',
    icon: Icons.person_outline,
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
    hit.kind == 'fixed_income' ? '/carteira/renda-fixa' : '/ativo/${hit.ref}';

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
        padding: const EdgeInsets.symmetric(vertical: FiSpace.s2),
        children: [
          for (final grupo in grupos) ...[
            _Cabecalho(texto: grupo.label, cor: ink3),
            ...grupo.items.map(
              (hit) => ListTile(
                leading: Icon(
                  hit.kind == 'fixed_income'
                      ? Icons.account_balance_outlined
                      : Icons.show_chart,
                ),
                title: Text(hit.title),
                subtitle: Text(hit.subtitle),
                onTap: () => context.go(rotaDoAchado(hit)),
              ),
            ),
          ],

          if (destinos.isNotEmpty) ...[
            _Cabecalho(texto: 'IR PARA', cor: ink3),
            ...destinos.map(
              (d) => ListTile(
                leading: Icon(d.icon),
                title: Text(d.title),
                subtitle: Text(d.subtitle),
                onTap: () => context.go(d.route),
              ),
            ),
          ],

          if (_error != null && destinos.isEmpty)
            Padding(
              padding: const EdgeInsets.all(FiSpace.s4),
              child: FiErrorState(error: _error!, action: 'buscar'),
            ),

          if (_query.trim().length >= 2 &&
              grupos.isEmpty &&
              destinos.isEmpty &&
              _error == null)
            Padding(
              padding: const EdgeInsets.all(FiSpace.s4),
              child: Text(
                'Nada encontrado para "${_query.trim()}".',
                style: FiType.body.copyWith(color: ink3),
              ),
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
      padding: const EdgeInsets.fromLTRB(
        FiSpace.s4,
        FiSpace.s3,
        FiSpace.s4,
        FiSpace.s1,
      ),
      child: Text(
        texto.toUpperCase(),
        style: FiType.eyebrow.copyWith(color: cor),
      ),
    );
  }
}
