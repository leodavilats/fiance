import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/cash_models.dart';
import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/mes.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';

/// Repetir o mes anterior: **previa e commit**, como a importacao de extrato.
///
/// `GET /cashflow/month/template` le e nao grava; `POST /cashflow/entries/batch` grava o lote
/// inteiro ou nenhum. Meio molde de mes e pior que molde nenhum, porque quem lancou nao teria
/// como saber o que entrou e o que ficou de fora.
///
/// **Vem marcado so o que repete por natureza.** Gasto variavel fica visivel e desmarcado,
/// porque o valor do mes que passou e fato daquele mes -- copia-lo inventaria despesa. E o
/// copiado nasce a vencer.
Future<void> abrirMoldeSheet(BuildContext context, WidgetRef ref) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (context) => const _MoldeSheet(),
  );
}

class _MoldeSheet extends ConsumerStatefulWidget {
  const _MoldeSheet();

  @override
  ConsumerState<_MoldeSheet> createState() => _MoldeSheetState();
}

class _MoldeSheetState extends ConsumerState<_MoldeSheet> {
  CashMonthTemplate? _molde;
  Set<int> _escolhidos = {};
  Object? _erro;
  bool _salvando = false;

  @override
  void initState() {
    super.initState();
    _carregar();
  }

  Future<void> _carregar() async {
    final alvo = ref.read(mesEscolhidoProvider);
    try {
      final m = await ref
          .read(apiRepositoryProvider)
          .getMonthTemplate(target: alvo, source: mesAnterior(alvo));
      if (!mounted) return;
      setState(() {
        _molde = m;
        // O que repete por natureza vem marcado; o que ja esta la nao se oferece de novo.
        _escolhidos = {
          for (var i = 0; i < m.candidates.length; i++)
            if (m.candidates[i].repeats && !m.candidates[i].alreadyThere) i,
        };
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _erro = e);
    }
  }

  Future<void> _gravar() async {
    final m = _molde;
    if (m == null || _escolhidos.isEmpty) return;

    setState(() => _salvando = true);
    try {
      final lote = [for (final i in _escolhidos) m.candidates[i]];
      await ref.read(apiRepositoryProvider).createCashEntriesBatch(lote);

      ref.invalidate(cashMonthProvider);
      ref.invalidate(cashEntriesProvider);
      ref.invalidate(surplusProvider);

      if (!mounted) return;
      final quantos = lote.length;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            '$quantos ${quantos == 1 ? 'lançamento copiado' : 'lançamentos copiados'} '
            'para ${nomeDoMes(m.target)}',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _salvando = false;
        _erro = e;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final erro = _erro;
    if (erro != null) {
      return SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: FiErrorState(
            error: erro,
            action: 'montar o molde do mês',
            onRetry: () {
              setState(() => _erro = null);
              _carregar();
            },
          ),
        ),
      );
    }

    final m = _molde;
    if (m == null) {
      return const SafeArea(
        child: Padding(
          padding: EdgeInsets.all(40),
          child: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    final disponiveis = [
      for (var i = 0; i < m.candidates.length; i++)
        if (!m.candidates[i].alreadyThere) i,
    ];

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Repetir ${nomeDoMes(m.source)}', style: FiType.title),
            const SizedBox(height: FiSpace.s2),
            Text(
              disponiveis.isEmpty
                  ? 'Tudo que ${nomeDoMes(m.source)} tinha já está em ${nomeDoMes(m.target)}.'
                  : 'Vem marcado o que repete todo mês. O gasto variável fica desmarcado: o '
                        'valor do mês que passou é fato daquele mês.',
              style: FiType.body.copyWith(color: fiInk2(context)),
            ),
            const SizedBox(height: FiSpace.s3),

            Flexible(
              child: ListView(
                shrinkWrap: true,
                children: [
                  for (final i in disponiveis)
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      dense: true,
                      value: _escolhidos.contains(i),
                      onChanged: (v) => setState(() {
                        if (v ?? false) {
                          _escolhidos.add(i);
                        } else {
                          _escolhidos.remove(i);
                        }
                      }),
                      title: Text(
                        m.candidates[i].description,
                        style: FiType.body,
                      ),
                      subtitle: Text(
                        '${formatCurrency(m.candidates[i].amount)} · '
                        '${cashCategoryLabel(m.candidates[i].kind, m.candidates[i].category)}'
                        '${m.candidates[i].repeats ? '' : ' · variável'}',
                        style: FiType.caption.copyWith(color: fiInk3(context)),
                      ),
                    ),
                ],
              ),
            ),

            const SizedBox(height: FiSpace.s4),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _salvando || _escolhidos.isEmpty ? null : _gravar,
                child: Text(
                  _salvando
                      ? 'Copiando…'
                      : _escolhidos.isEmpty
                      ? 'Escolha o que copiar'
                      : 'Copiar ${_escolhidos.length} para ${nomeDoMes(m.target)}',
                ),
              ),
            ),
            if (_escolhidos.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: FiSpace.s2),
                child: Text(
                  'Tudo de uma vez, ou nada. O copiado nasce a vencer.',
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
