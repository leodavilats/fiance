import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/vocabulary.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/disclosure.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';

Future<void> openDividendForm(BuildContext context, WidgetRef ref) async {
  final salvo = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.9),
    builder: (context) => Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: const _DividendForm(),
    ),
  );

  if (salvo == true) {
    ref.invalidate(dividendsProvider);
    ref.invalidate(pendingDividendsProvider);
    ref.invalidate(dashboardProvider);
  }
}

class DividendsScreen extends ConsumerWidget {
  const DividendsScreen({super.key});

  Future<void> _delete(BuildContext context, WidgetRef ref, DividendReceived item) async {
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Apagar provento de ${item.ticker}?'),
        content: const Text(
          'O valor sai do histórico e da renda do mês em que foi creditado.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Apagar'),
          ),
        ],
      ),
    );
    if (confirmado != true) return;

    try {
      await ref.read(apiRepositoryProvider).deleteDividendReceived(item.id);
      ref.invalidate(dividendsProvider);
      ref.invalidate(dashboardProvider);
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(fiErrorMessage(e, action: 'apagar este provento'))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recebidos = ref.watch(dividendsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Proventos')),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(dividendsProvider);
          ref.invalidate(pendingDividendsProvider);
        },
        child: recebidos.when(
          loading: () => FiSkeleton.screen(
            shape: FiSkeletonShape.row,
            count: 6,
            label: 'Carregando seus proventos',
          ),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos carregar seus proventos',
            action: 'carregar os proventos recebidos',
            onRetry: () => ref.invalidate(dividendsProvider),
          ),
          data: (data) {
            if (data.items.isEmpty) {
              return ListView(
                padding: const EdgeInsets.fromLTRB(
                  FiLayout.gutter,
                  FiSpace.s3,
                  FiLayout.gutter,
                  FiLayout.scrollTail,
                ),
                children: [
                  FiEmptyState(
                    title: 'Nenhum provento registrado',
                    body: 'Provento creditado é lançamento do razão, e é ele que alimenta a '
                        'renda do mês. Não se lança no caixa: contaria o mesmo dinheiro duas '
                        'vezes.',
                    hint: 'Registre o que já caiu na conta, ou confirme abaixo o que o seu '
                        'razão já prova que é seu.',
                    action: FiButton.primary(
                      label: 'Registrar provento',
                      icon: Icons.add,
                      onPressed: () => openDividendForm(context, ref),
                    ),
                  ),
                  const SizedBox(height: FiSpace.s5),
                  const _AwaitingConfirmation(),
                  const _Calendar(),
                ],
              );
            }

            return ListView(
              padding: const EdgeInsets.fromLTRB(
                FiLayout.gutter,
                FiSpace.s3,
                FiLayout.gutter,
                FiLayout.scrollTail,
              ),
              children: [
                _Totals(data: data),
                const _AwaitingConfirmation(),
                const _Calendar(),
                FiSection(
                  title: 'Recebidos',
                  count: data.totalCount,
                  trailing: FiButton.quiet(
                    label: 'Registrar',
                    icon: Icons.add,
                    onPressed: () => openDividendForm(context, ref),
                  ),
                  child: Column(
                    children: [
                      for (final item in data.items)
                        _DividendObject(
                          item: item,
                          onDelete: () => _delete(context, ref, item),
                        ),
                    ],
                  ),
                ),
                if (data.byTicker.isNotEmpty)
                  FiSection(
                    title: 'Por ativo',
                    hint: 'Quem paga quanto, nos últimos 12 meses.',
                    child: FiRows(
                      children: [
                        for (final t in data.byTicker.take(12))
                          FiDataRow(
                            label: t.ticker,
                            value: formatCurrency(t.total),
                            detail: '${t.count} ${t.count == 1 ? 'crédito' : 'créditos'}',
                          ),
                      ],
                    ),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _Totals extends StatelessWidget {
  const _Totals({required this.data});

  final DividendsReceived data;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        FiHeadline(
          eyebrow: 'Recebido nos últimos 12 meses',
          figure: formatCurrency(data.receivedLast12m),
          size: FiHeadlineSize.xl,
          support: '${formatCurrency(data.monthlyAverage12m)} por mês, em média',
        ),
        const SizedBox(height: FiSpace.s5),
        FiFigures(
          figures: {
            'NESTE MÊS': formatCurrency(data.receivedThisMonth),
            'TOTAL REGISTRADO': formatCurrency(data.totalReceived),
          },
        ),
        const SizedBox(height: FiSpace.s3),
        const FiProvenance(
          summary: 'De onde vem este número',
          method: 'Soma dos proventos que você registrou, por mês de crédito. A média é dos '
              'últimos 12 meses corridos.',
          source: 'Seus lançamentos — registrados aqui ou confirmados a partir do calendário '
              'da fonte.',
          limitation: 'Só entra o que foi registrado. Provento creditado e não lançado não '
              'aparece, e a média sai menor do que a real.',
        ),
      ],
    );
  }
}

class _DividendObject extends StatelessWidget {
  const _DividendObject({required this.item, required this.onDelete});

  final DividendReceived item;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    item.ticker,
                    style: FiType.title.copyWith(color: fiInk1(context)),
                  ),
                ),
                const SizedBox(width: FiSpace.s2),
                FiTag.series(
                  label: dividendKindLabel(item.kind),
                  color: fiInk2(context),
                ),
                IconButton(
                  onPressed: onDelete,
                  icon: const Icon(Icons.delete_outline),
                  tooltip: 'Apagar provento',
                  iconSize: 20,
                ),
              ],
            ),
            FiRows(
              children: [
                FiDataRow(label: 'Crédito', value: formatDate(item.paidAt)),
                FiDataRow(
                  label: 'Valor líquido',
                  value: formatCurrency(item.amount),
                  emphasis: true,
                ),
              ],
            ),
            if ((item.note ?? '').isNotEmpty) ...[
              const SizedBox(height: FiSpace.s2),
              Text(
                item.note!,
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _AwaitingConfirmation extends ConsumerWidget {
  const _AwaitingConfirmation();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pendentes = ref.watch(pendingDividendsProvider);

    return pendentes.maybeWhen(
      loading: () => const FiSection(
        title: 'Confirme o que já caiu',
        child: FiSkeleton(shape: FiSkeletonShape.row, count: 2),
      ),
      data: (data) {
        final provados = data.items.where((s) => s.entitlementProven).toList();
        if (provados.isEmpty) return const SizedBox.shrink();

        return _SuggestionList(
          title: 'Confirme o que já caiu',
          suggestions: provados,
          hint: 'O seu razão mostra a posição já na data-com, então estes proventos são seus. '
              'Falta só dizer que caíram na conta — nada é lançado antes disso.',
          collapsed: false,
        );
      },
      orElse: () => const SizedBox.shrink(),
    );
  }
}

class _Calendar extends ConsumerWidget {
  const _Calendar();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pendentes = ref.watch(pendingDividendsProvider);

    return pendentes.when(
      loading: () => const FiSection(
        title: 'Consultar o calendário',
        child: FiSkeleton(shape: FiSkeletonShape.row, count: 1),
      ),
      error: (err, _) => FiErrorState(
        error: err,
        title: 'Não conseguimos ler o calendário de proventos',
        action: 'buscar proventos do calendário',
        onRetry: () => ref.invalidate(pendingDividendsProvider),
      ),
      data: (data) {
        final indeterminados =
            data.items.where((s) => !s.entitlementProven).toList();
        if (indeterminados.isEmpty) return const SizedBox.shrink();

        return _SuggestionList(
          title: 'Consultar o calendário',
          suggestions: indeterminados,
          hint: 'Aqui o razão não prova o direito: ou a fonte não publicou a data-com, ou os '
              'seus lançamentos não alcançam aquela data. Confira contra o extrato da '
              'corretora antes de confirmar.',
          collapsed: true,
        );
      },
    );
  }
}

class _SuggestionList extends ConsumerStatefulWidget {
  const _SuggestionList({
    required this.title,
    required this.suggestions,
    required this.hint,
    required this.collapsed,
  });

  final String title;
  final List<DividendSuggestion> suggestions;
  final String hint;
  final bool collapsed;

  @override
  ConsumerState<_SuggestionList> createState() => _SuggestionListState();
}

class _SuggestionListState extends ConsumerState<_SuggestionList> {
  final Set<String> _chosen = {};
  bool _confirming = false;

  String _key(DividendSuggestion s) => '${s.ticker}|${s.paidAt}';

  Future<void> _confirm() async {
    final selecionados = widget.suggestions
        .where((s) => _chosen.contains(_key(s)))
        .toList();
    if (selecionados.isEmpty) return;

    setState(() => _confirming = true);
    try {
      final criados = await ref
          .read(apiRepositoryProvider)
          .confirmDividends(selecionados);
      _chosen.clear();
      ref.invalidate(dividendsProvider);
      ref.invalidate(pendingDividendsProvider);
      ref.invalidate(dashboardProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              '$criados ${criados == 1 ? 'provento lançado' : 'proventos lançados'}.',
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              fiErrorMessage(e, action: 'lançar os proventos escolhidos'),
            ),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _confirming = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final marcados = widget.suggestions
        .where((s) => _chosen.contains(_key(s)))
        .toList();
    final chosen = marcados.length;
    final somaMarcada = marcados.fold<double>(0, (t, s) => t + s.amount);
    final total = widget.suggestions.fold<double>(0, (t, s) => t + s.amount);
    final todos = chosen == widget.suggestions.length;

    final corpo = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (widget.suggestions.length > 1)
          Padding(
            padding: const EdgeInsets.only(bottom: FiSpace.s2),
            child: Align(
              alignment: Alignment.centerLeft,
              child: FiButton.quiet(
                label: todos ? 'Desmarcar todos' : 'Marcar todos',
                onPressed: () => setState(() {
                  _chosen.clear();
                  if (!todos) {
                    _chosen.addAll(widget.suggestions.map(_key));
                  }
                }),
              ),
            ),
          ),
        for (final s in widget.suggestions)
          _SuggestionObject(
            suggestion: s,
            checked: _chosen.contains(_key(s)),
            onToggle: () => setState(() {
              final k = _key(s);
              if (!_chosen.remove(k)) _chosen.add(k);
            }),
          ),
        const SizedBox(height: FiSpace.s3),
        Text(
          chosen == 0
              ? 'Marque o que já caiu na conta. O que ficar desmarcado não é lançado.'
              : '$chosen de ${widget.suggestions.length} marcados, '
                    '${formatCurrency(somaMarcada)} no total.',
          style: FiType.caption.copyWith(color: fiInk3(context)),
        ),
        const SizedBox(height: FiSpace.s2),
        FiButton.primary(
          label: _confirming
              ? 'Lançando…'
              : chosen == 0
              ? 'Lançar os marcados'
              : 'Lançar $chosen ${chosen == 1 ? 'provento' : 'proventos'}',
          busy: _confirming,
          onPressed: _confirming || chosen == 0 ? null : _confirm,
        ),
      ],
    );

    if (!widget.collapsed) {
      return FiSection(
        title: widget.title,
        count: widget.suggestions.length,
        hint: widget.hint,
        child: corpo,
      );
    }

    return FiSection(
      title: widget.title,
      count: widget.suggestions.length,
      child: FiDisclosure(
        rule: false,
        title:
            '${widget.suggestions.length} '
            '${widget.suggestions.length == 1 ? 'crédito' : 'créditos'} '
            'que o razão não confirma',
        detail: widget.suggestions.length == 1
            ? 'Um crédito por conferir'
            : 'Somam ${formatCurrency(total)} por conferir',
        initiallyOpen: false,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.hint,
              style: FiType.caption.copyWith(color: fiInk3(context)),
            ),
            const SizedBox(height: FiSpace.s3),
            corpo,
          ],
        ),
      ),
    );
  }
}

class _SuggestionObject extends StatelessWidget {
  const _SuggestionObject({
    required this.suggestion,
    required this.checked,
    required this.onToggle,
  });

  final DividendSuggestion suggestion;
  final bool checked;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        onTap: onToggle,
        accent: checked ? fiStateColor(FiState.favorable, brightness) : null,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Semantics(
                  label: checked
                      ? 'Desmarcar provento de ${suggestion.ticker}'
                      : 'Marcar provento de ${suggestion.ticker} como recebido',
                  child: Checkbox(value: checked, onChanged: (_) => onToggle()),
                ),
                Expanded(
                  child: Text(
                    suggestion.ticker,
                    style: FiType.title.copyWith(color: fiInk1(context)),
                  ),
                ),
                const SizedBox(width: FiSpace.s2),
                FiTag.series(
                  label: dividendKindLabel(suggestion.kind),
                  color: fiInk2(context),
                ),
              ],
            ),
            FiRows(
              children: [
                FiDataRow(label: 'Crédito', value: formatDate(suggestion.paidAt)),
                if (suggestion.exDate != null)
                  FiDataRow(
                    label: 'Data-com',
                    value: formatDate(suggestion.exDate),
                    detail: 'quem tinha o ativo neste dia recebe',
                  ),
                FiDataRow(
                  label: 'Valor estimado',
                  value: formatCurrency(suggestion.amount),
                  emphasis: true,
                ),
                FiDataRow(
                  label: 'Base do cálculo',
                  value: '${formatQuantity(suggestion.quantityAtDate)} × '
                      '${formatCurrency(suggestion.ratePerShare)}',
                  detail: suggestion.quantityIsCurrent
                      ? 'Quantidade de hoje, não a da data-com'
                      : 'Quantidade que o seu razão tinha na data-com',
                ),
              ],
            ),
            if (suggestion.caveats.isNotEmpty) ...[
              const SizedBox(height: FiSpace.s2),
              for (final c in suggestion.caveats)
                Padding(
                  padding: const EdgeInsets.only(bottom: FiSpace.s1),
                  child: Text(
                    '• $c',
                    style: FiType.caption.copyWith(
                      color: fiStateColor(FiState.attention, brightness),
                    ),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _DividendForm extends ConsumerStatefulWidget {
  const _DividendForm();

  @override
  ConsumerState<_DividendForm> createState() => _DividendFormState();
}

class _DividendFormState extends ConsumerState<_DividendForm> {
  final _formKey = GlobalKey<FormState>();
  final _ticker = TextEditingController();
  final _amount = TextEditingController();
  final _note = TextEditingController();

  String _kind = 'dividendo';
  DateTime _date = DateTime.now();
  bool _saving = false;

  @override
  void dispose() {
    _ticker.dispose();
    _amount.dispose();
    _note.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() => _saving = true);
    try {
      await ref
          .read(apiRepositoryProvider)
          .createDividendReceived(
            ticker: _ticker.text.trim().toUpperCase(),
            paidAt: _date.toIso8601String().substring(0, 10),
            amount: double.parse(_amount.text.trim().replaceAll(',', '.')),
            kind: _kind,
            note: _note.text.trim().isEmpty ? null : _note.text.trim(),
          );
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() => _saving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(fiErrorMessage(e, action: 'registrar o provento'))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          FiSpace.s5,
        ),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Provento recebido',
                style: FiType.title.copyWith(color: fiInk1(context)),
              ),
              const SizedBox(height: FiSpace.s2),
              Text(
                'O valor líquido que caiu na conta. Ele entra na renda do mês do crédito.',
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
              const SizedBox(height: FiSpace.s4),
              TickerAutocompleteField(controller: _ticker),
              const SizedBox(height: FiSpace.s3),
              DropdownButtonFormField<String>(
                initialValue: _kind,
                decoration: const InputDecoration(labelText: 'Tipo'),
                items: [
                  for (final e in fiDividendKinds.entries)
                    DropdownMenuItem(value: e.key, child: Text(e.value)),
                ],
                onChanged: (v) => setState(() => _kind = v ?? 'dividendo'),
              ),
              const SizedBox(height: FiSpace.s3),
              InputDecorator(
                decoration: const InputDecoration(labelText: 'Data do crédito'),
                child: InkWell(
                  onTap: () async {
                    final escolhida = await showDatePicker(
                      context: context,
                      initialDate: _date,
                      firstDate: DateTime(2000),
                      lastDate: DateTime.now(),
                    );
                    if (escolhida != null) setState(() => _date = escolhida);
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: FiSpace.s1),
                    child: Text(
                      formatDate(_date.toIso8601String().substring(0, 10)),
                      style: FiType.body.copyWith(color: fiInk1(context)),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: FiSpace.s3),
              TextFormField(
                controller: _amount,
                decoration: const InputDecoration(
                  labelText: 'Valor líquido',
                  prefixText: 'R\$ ',
                  helperText: 'O que entrou na conta, já com IR retido quando houver.',
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                validator: (v) {
                  final n = double.tryParse((v ?? '').replaceAll(',', '.'));
                  if (n == null || n <= 0) return 'Informe um valor positivo';
                  return null;
                },
              ),
              const SizedBox(height: FiSpace.s3),
              TextFormField(
                controller: _note,
                decoration: const InputDecoration(labelText: 'Observação (opcional)'),
              ),
              const SizedBox(height: FiSpace.s5),
              FiButton.primary(
                label: _saving ? 'Registrando…' : 'Registrar provento',
                onPressed: _saving ? null : _save,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
