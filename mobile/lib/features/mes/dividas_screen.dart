import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/cash_models.dart';
import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/vocabulary.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';

/// As dividas: saldo, taxa, e a comparacao com o que a carteira rende.
class DividasScreen extends ConsumerWidget {
  const DividasScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dividas = ref.watch(debtsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Dívidas')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _abrirCadastro(context, ref),
        icon: const Icon(Icons.add),
        label: const Text('Cadastrar'),
      ),
      body: dividas.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => FiErrorState(
          error: e,
          action: 'carregar suas dívidas',
          onRetry: () => ref.invalidate(debtsProvider),
        ),
        data: (lista) => lista.isEmpty
            ? const _SemDivida()
            : _Lista(dividas: lista),
      ),
    );
  }

  Future<void> _abrirCadastro(BuildContext context, WidgetRef ref) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: const _CadastroForm(),
      ),
    );
  }
}

class _Lista extends ConsumerWidget {
  const _Lista({required this.dividas});

  final List<Debt> dividas;

  static const _rotuloDaClasse = {
    DebtClass.expensive: 'Caseira',
    DebtClass.manageable: 'Administrável',
    DebtClass.noRate: 'Sem taxa informada',
  };

  static FiState _estado(DebtClass c) => switch (c) {
    DebtClass.expensive => FiState.adverse,
    DebtClass.manageable => FiState.neutral,
    DebtClass.noRate => FiState.indeterminate,
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final brightness = Theme.of(context).brightness;
    final caras = dividas.where((d) => d.debtClass == DebtClass.expensive);
    final referencia = dividas
        .map((d) => d.referenceMonthly)
        .firstWhere((r) => r != null, orElse: () => null);

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(debtsProvider),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 88),
        children: [
          Text(
            caras.isEmpty
                ? 'Nenhuma dívida sua custa mais do que sua carteira rende.'
                : 'Você tem ${caras.length} '
                      '${caras.length == 1 ? 'dívida' : 'dívidas'} que custam mais do que sua '
                      'carteira rende.',
            style: FiType.verdict.copyWith(fontFamily: fiFontSerif),
          ),

          FiProvenance(
            summary: 'Como classificamos',
            method:
                'Compara a taxa mensal de cada dívida com o que sua carteira rende ao mês. '
                'Acima disso, pagar a dívida rende mais que investir.',
            source: referencia == null
                ? 'Sem taxa informada em nenhuma dívida, não há o que comparar.'
                : 'Referência: ${formatPercent(referencia)} ao mês, de '
                      '${dividas.first.referenceSource == 'bcb' ? 'CDI do BCB' : dividas.first.referenceSource}.',
            limitation:
                'Dívida sem taxa informada fica sem classe: o produto não estima taxa de '
                'rotativo, que varia por banco e por dia.',
          ),

          FiSection(
            title: 'Suas dívidas',
            count: dividas.length,
            child: Column(
              children: [
                for (final d in dividas)
                  _LinhaDivida(
                    divida: d,
                    rotulo: _rotuloDaClasse[d.debtClass] ?? '',
                    cor: fiStateColor(_estado(d.debtClass), brightness),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _LinhaDivida extends ConsumerWidget {
  const _LinhaDivida({
    required this.divida,
    required this.rotulo,
    required this.cor,
  });

  final Debt divida;
  final String rotulo;
  final Color cor;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      shape: const Border(),
      collapsedShape: const Border(),
      title: Text(divida.description, style: FiType.body),
      subtitle: Text(
        '${debtKindLabel(divida.kind)} · $rotulo',
        style: FiType.caption.copyWith(color: cor),
      ),
      trailing: Text(formatCurrency(divida.balance), style: FiType.metricSm),
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: FiSpace.s3),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                divida.monthlyRate == null
                    ? 'Taxa não informada, então não há classe.'
                    : 'Custa ${formatPercent(divida.monthlyRate)} ao mês.',
                style: FiType.body.copyWith(color: fiInk2(context)),
              ),
              if (divida.flipRate != null)
                Text(
                  'Vira administrável a ${formatPercent(divida.flipRate)} ao mês.',
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
              const SizedBox(height: FiSpace.s2),
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton(
                  onPressed: divida.id == null
                      ? null
                      : () => _quitar(context, ref, divida),
                  child: const Text('Marcar como quitada'),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _quitar(BuildContext context, WidgetRef ref, Debt d) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Quitar esta dívida?'),
        content: Text(
          '${d.description} sai da sua ordem de sobra, e o veredito do mês passa a não '
          'contá-la.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Quitar dívida'),
          ),
        ],
      ),
    );
    if (ok != true) return;

    await ref.read(apiRepositoryProvider).settleDebt(d.id!);
    ref.invalidate(debtsProvider);
    ref.invalidate(surplusProvider);
    ref.invalidate(cashMonthProvider);
  }
}

class _CadastroForm extends ConsumerStatefulWidget {
  const _CadastroForm();

  @override
  ConsumerState<_CadastroForm> createState() => _CadastroFormState();
}

class _CadastroFormState extends ConsumerState<_CadastroForm> {
  final _form = GlobalKey<FormState>();
  final _descricao = TextEditingController();
  final _saldo = TextEditingController();
  final _taxa = TextEditingController();

  String _tipo = fiTiposDeDivida.keys.first;
  bool _salvando = false;
  Object? _erro;

  @override
  void dispose() {
    _descricao.dispose();
    _saldo.dispose();
    _taxa.dispose();
    super.dispose();
  }

  Future<void> _salvar() async {
    if (!_form.currentState!.validate()) return;

    final saldo = double.tryParse(
      _saldo.text.replaceAll('.', '').replaceAll(',', '.'),
    );
    if (saldo == null) return;

    final taxaTexto = _taxa.text.trim();
    final taxa = taxaTexto.isEmpty
        ? null
        : double.tryParse(taxaTexto.replaceAll(',', '.'));

    setState(() => _salvando = true);
    try {
      await ref.read(apiRepositoryProvider).createDebt(
        kind: _tipo,
        description: _descricao.text.trim(),
        balance: saldo,
        monthlyRate: taxa,
      );
      ref.invalidate(debtsProvider);
      ref.invalidate(surplusProvider);
      ref.invalidate(cashMonthProvider);

      if (!mounted) return;
      Navigator.of(context).pop();
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
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Form(
          key: _form,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Cadastrar dívida', style: FiType.title),
              const SizedBox(height: FiSpace.s4),

              TextFormField(
                controller: _descricao,
                decoration: const InputDecoration(labelText: 'Descrição'),
                textCapitalization: TextCapitalization.sentences,
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Diga o que é' : null,
              ),
              const SizedBox(height: FiSpace.s3),

              DropdownButtonFormField<String>(
                initialValue: _tipo,
                decoration: const InputDecoration(labelText: 'Tipo'),
                items: [
                  for (final e in fiTiposDeDivida.entries)
                    DropdownMenuItem(value: e.key, child: Text(e.value)),
                ],
                onChanged: (v) => setState(() => _tipo = v ?? _tipo),
              ),
              const SizedBox(height: FiSpace.s3),

              TextFormField(
                controller: _saldo,
                decoration: const InputDecoration(
                  labelText: 'Saldo devedor',
                  prefixText: r'R$ ',
                ),
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                validator: (v) {
                  final n = double.tryParse(
                    (v ?? '').replaceAll('.', '').replaceAll(',', '.'),
                  );
                  if (n == null || n <= 0) return 'Um valor positivo';
                  return null;
                },
              ),
              const SizedBox(height: FiSpace.s3),

              TextFormField(
                controller: _taxa,
                decoration: const InputDecoration(
                  labelText: 'Taxa mensal (opcional)',
                  suffixText: '% ao mês',
                  helperText:
                      'Sem a taxa não há classe: o produto não estima taxa de rotativo.',
                  helperMaxLines: 2,
                ),
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
              ),

              if (_erro != null) ...[
                const SizedBox(height: FiSpace.s3),
                Text(
                  fiErrorMessage(_erro!, action: 'cadastrar esta dívida'),
                  style: FiType.body.copyWith(
                    color: fiStateColor(
                      FiState.adverse,
                      Theme.of(context).brightness,
                    ),
                  ),
                ),
              ],

              const SizedBox(height: FiSpace.s5),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _salvando ? null : _salvar,
                  child: Text(_salvando ? 'Salvando…' : 'Cadastrar'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SemDivida extends StatelessWidget {
  const _SemDivida();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(
          'Você não tem dívida cadastrada',
          style: FiType.verdict.copyWith(fontFamily: fiFontSerif),
        ),
        const SizedBox(height: FiSpace.s3),
        Text(
          'A ordem da sobra começa pela dívida que custa mais do que sua carteira rende. Sem '
          'cadastrar, ela não entra na conta — e é a que decide se aportar faz sentido.',
          style: FiType.body.copyWith(color: fiInk2(context)),
        ),
      ],
    );
  }
}
