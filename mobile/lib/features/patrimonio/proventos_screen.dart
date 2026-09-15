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
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';

Future<void> abrirFormDeProvento(BuildContext context, WidgetRef ref) async {
  final salvo = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.9),
    builder: (context) => Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: const _ProventoForm(),
    ),
  );

  if (salvo == true) {
    ref.invalidate(proventosProvider);
    ref.invalidate(proventosPendentesProvider);
    ref.invalidate(dashboardProvider);
  }
}

class ProventosScreen extends ConsumerWidget {
  const ProventosScreen({super.key});

  Future<void> _apagar(BuildContext context, WidgetRef ref, DividendReceived item) async {
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
      ref.invalidate(proventosProvider);
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
    final recebidos = ref.watch(proventosProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Proventos')),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(proventosProvider);
          ref.invalidate(proventosPendentesProvider);
        },
        child: recebidos.when(
          loading: () => FiSkeleton.tela(
            shape: FiSkeletonShape.row,
            count: 6,
            label: 'Carregando seus proventos',
          ),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos carregar seus proventos',
            action: 'carregar os proventos recebidos',
            onRetry: () => ref.invalidate(proventosProvider),
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
                    hint: 'Registre o que já caiu na conta, ou confira as sugestões abaixo.',
                    action: FiButton.primary(
                      label: 'Registrar provento',
                      icon: Icons.add,
                      onPressed: () => abrirFormDeProvento(context, ref),
                    ),
                  ),
                  const SizedBox(height: FiSpace.s5),
                  const _Pendentes(),
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
                _Totais(data: data),
                const SizedBox(height: FiSpace.s5),
                const _Pendentes(),
                FiSection(
                  title: 'Recebidos',
                  count: data.totalCount,
                  action: FiButton.secondary(
                    label: 'Registrar',
                    icon: Icons.add,
                    onPressed: () => abrirFormDeProvento(context, ref),
                  ),
                  child: Column(
                    children: [
                      for (final item in data.items)
                        _ProventoObject(
                          item: item,
                          onDelete: () => _apagar(context, ref, item),
                        ),
                    ],
                  ),
                ),
                if (data.byTicker.isNotEmpty)
                  FiSection(
                    title: 'Por ativo',
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

class _Totais extends StatelessWidget {
  const _Totais({required this.data});

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

class _ProventoObject extends StatelessWidget {
  const _ProventoObject({required this.item, required this.onDelete});

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
                FiTag.serie(
                  label: proventoTipoLabel(item.kind),
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

class _Pendentes extends ConsumerStatefulWidget {
  const _Pendentes();

  @override
  ConsumerState<_Pendentes> createState() => _PendentesState();
}

class _PendentesState extends ConsumerState<_Pendentes> {
  final Set<String> _escolhidos = {};
  bool _confirmando = false;

  String _chave(DividendSuggestion s) => '${s.ticker}|${s.paidAt}';

  Future<void> _confirmar(List<DividendSuggestion> todos) async {
    final selecionados = todos.where((s) => _escolhidos.contains(_chave(s))).toList();
    if (selecionados.isEmpty) return;

    setState(() => _confirmando = true);
    try {
      final criados = await ref.read(apiRepositoryProvider).confirmDividends(selecionados);
      _escolhidos.clear();
      ref.invalidate(proventosProvider);
      ref.invalidate(proventosPendentesProvider);
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
          SnackBar(content: Text(fiErrorMessage(e, action: 'lançar os proventos escolhidos'))),
        );
      }
    } finally {
      if (mounted) setState(() => _confirmando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pendentes = ref.watch(proventosPendentesProvider);

    return pendentes.when(
      loading: () => FiSection(
        title: 'Sugestões do calendário',
        child: Semantics(
          label: 'Procurando proventos no calendário',
          liveRegion: true,
          child: const FiSkeleton(shape: FiSkeletonShape.row, count: 2),
        ),
      ),
      error: (err, _) => FiErrorState(
        error: err,
        title: 'Não conseguimos ler o calendário de proventos',
        action: 'buscar proventos do calendário',
        onRetry: () => ref.invalidate(proventosPendentesProvider),
      ),
      data: (data) {
        if (data.items.isEmpty) return const SizedBox.shrink();

        final escolhidos = data.items.where((s) => _escolhidos.contains(_chave(s))).length;

        return FiSection(
          title: 'Sugestões do calendário',
          count: data.items.length,
          hint: 'Nada foi lançado. Confira cada linha contra o extrato da corretora antes de '
              'confirmar — a quantidade vem da sua posição, e o calendário da fonte.',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final s in data.items)
                _SugestaoObject(
                  sugestao: s,
                  marcada: _escolhidos.contains(_chave(s)),
                  onToggle: () => setState(() {
                    final k = _chave(s);
                    if (!_escolhidos.remove(k)) _escolhidos.add(k);
                  }),
                ),
              const SizedBox(height: FiSpace.s3),
              FiButton.primary(
                label: _confirmando
                    ? 'Lançando…'
                    : escolhidos == 0
                    ? 'Marque o que já caiu na conta'
                    : 'Lançar $escolhidos ${escolhidos == 1 ? 'provento' : 'proventos'}',
                onPressed: _confirmando || escolhidos == 0
                    ? null
                    : () => _confirmar(data.items),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _SugestaoObject extends StatelessWidget {
  const _SugestaoObject({
    required this.sugestao,
    required this.marcada,
    required this.onToggle,
  });

  final DividendSuggestion sugestao;
  final bool marcada;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        accent: marcada ? fiStateColor(FiState.favorable, brightness) : null,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Semantics(
                  label: marcada
                      ? 'Desmarcar provento de ${sugestao.ticker}'
                      : 'Marcar provento de ${sugestao.ticker} como recebido',
                  child: Checkbox(value: marcada, onChanged: (_) => onToggle()),
                ),
                Expanded(
                  child: Text(
                    sugestao.ticker,
                    style: FiType.title.copyWith(color: fiInk1(context)),
                  ),
                ),
                const SizedBox(width: FiSpace.s2),
                FiTag.serie(
                  label: proventoTipoLabel(sugestao.kind),
                  color: fiInk2(context),
                ),
              ],
            ),
            FiRows(
              children: [
                FiDataRow(label: 'Crédito', value: formatDate(sugestao.paidAt)),
                FiDataRow(
                  label: 'Valor estimado',
                  value: formatCurrency(sugestao.amount),
                  emphasis: true,
                ),
                FiDataRow(
                  label: 'Base do cálculo',
                  value: '${formatQuantity(sugestao.quantityAtDate)} × '
                      '${formatCurrency(sugestao.ratePerShare)}',
                  detail: sugestao.quantityIsCurrent
                      ? 'Quantidade de hoje, não a da data do crédito'
                      : 'Quantidade que você tinha na data',
                ),
              ],
            ),
            if (sugestao.caveats.isNotEmpty) ...[
              const SizedBox(height: FiSpace.s2),
              for (final c in sugestao.caveats)
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

class _ProventoForm extends ConsumerStatefulWidget {
  const _ProventoForm();

  @override
  ConsumerState<_ProventoForm> createState() => _ProventoFormState();
}

class _ProventoFormState extends ConsumerState<_ProventoForm> {
  final _formKey = GlobalKey<FormState>();
  final _ticker = TextEditingController();
  final _valor = TextEditingController();
  final _nota = TextEditingController();

  String _kind = 'dividendo';
  DateTime _data = DateTime.now();
  bool _salvando = false;

  @override
  void dispose() {
    _ticker.dispose();
    _valor.dispose();
    _nota.dispose();
    super.dispose();
  }

  Future<void> _salvar() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() => _salvando = true);
    try {
      await ref
          .read(apiRepositoryProvider)
          .createDividendReceived(
            ticker: _ticker.text.trim().toUpperCase(),
            paidAt: _data.toIso8601String().substring(0, 10),
            amount: double.parse(_valor.text.trim().replaceAll(',', '.')),
            kind: _kind,
            note: _nota.text.trim().isEmpty ? null : _nota.text.trim(),
          );
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() => _salvando = false);
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
                  for (final e in fiTiposDeProvento.entries)
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
                      initialDate: _data,
                      firstDate: DateTime(2000),
                      lastDate: DateTime.now(),
                    );
                    if (escolhida != null) setState(() => _data = escolhida);
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: FiSpace.s1),
                    child: Text(
                      formatDate(_data.toIso8601String().substring(0, 10)),
                      style: FiType.body.copyWith(color: fiInk1(context)),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: FiSpace.s3),
              TextFormField(
                controller: _valor,
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
                controller: _nota,
                decoration: const InputDecoration(labelText: 'Observação (opcional)'),
              ),
              const SizedBox(height: FiSpace.s5),
              FiButton.primary(
                label: _salvando ? 'Registrando…' : 'Registrar provento',
                onPressed: _salvando ? null : _salvar,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
