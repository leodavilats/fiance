import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/ledger_models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';

const _reasons = {
  'no_razao_sem_posicao': 'O razão tem esta posição aberta, e a carteira não a mostra.',
  'posicao_sem_razao': 'A carteira tem esta posição, e nenhum lançamento a sustenta.',
  'quantidade': 'A quantidade da carteira difere da que o razão projeta.',
  'preco_medio': 'O preço médio da carteira difere do que o razão projeta.',
};

class ReconciliationScreen extends ConsumerWidget {
  const ReconciliationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final conferencia = ref.watch(reconciliationProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Conferir com o razão')),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(reconciliationProvider),
        child: conferencia.when(
          loading: () => FiSkeleton.screen(
            shape: FiSkeletonShape.row,
            count: 4,
            label: 'Conferindo a carteira contra o razão',
          ),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos conferir a carteira',
            action: 'conferir a carteira contra o razão',
            onRetry: () => ref.invalidate(reconciliationProvider),
          ),
          data: (data) => ListView(
            padding: const EdgeInsets.fromLTRB(
              FiLayout.gutter,
              FiSpace.s3,
              FiLayout.gutter,
              FiSpace.s8,
            ),
            children: [
              Text(
                data.inSync
                    ? 'A carteira bate com o razão'
                    : data.differences.length == 1
                    ? '1 diferença entre a carteira e o razão'
                    : '${data.differences.length} diferenças entre a carteira e o razão',
                style: FiType.title.copyWith(color: fiInk1(context)),
              ),
              const SizedBox(height: FiSpace.s2),
              Text(
                data.inSync
                    ? '${data.positions} posição(ões) na carteira, e cada uma é exatamente o que '
                          'os lançamentos projetam.'
                    : 'A carteira devia ser só a projeção dos lançamentos. Onde ela diverge, o '
                          'razão é quem está certo — a menos que falte lançar alguma coisa.',
                style: FiType.body.copyWith(color: fiInk2(context)),
              ),
              const SizedBox(height: FiSpace.s2),
              const FiProvenance(
                summary: 'Como a conferência é feita',
                method: 'Cada lançamento do razão é reaplicado em ordem, pela convenção brasileira '
                    'de preço médio, e o resultado é comparado posição a posição com a carteira.',
                source: 'Seus lançamentos e a carteira gravada.',
                limitation: 'Diferença de centavos no preço médio e de frações de cota na '
                    'quantidade é tolerada: vem de arredondamento, não de lançamento faltando.',
              ),
              if (!data.inSync) ...[
                FiSection(
                  title: 'Diferenças',
                  count: data.differences.length,
                  child: Column(
                    children: [
                      for (final d in data.differences) _DifferenceObject(difference: d),
                    ],
                  ),
                ),
                _Actions(reconciliation: data),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _DifferenceObject extends StatelessWidget {
  const _DifferenceObject({required this.difference});

  final ReconciliationDifference difference;

  String _position(ReconciledPosition? p) => p == null
      ? '—'
      : '${formatQuantity(p.quantity)} × ${formatCurrency(p.avgPrice)}';

  @override
  Widget build(BuildContext context) {
    final d = difference;
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(d.ticker, style: FiType.title.copyWith(color: fiInk1(context))),
                ),
                if (d.positionWithoutLedger)
                  const FiTag(label: 'Sem lançamento', state: FiState.attention),
              ],
            ),
            const SizedBox(height: FiSpace.s1),
            Text(
              _reasons[d.reason] ?? d.reason,
              style: FiType.caption.copyWith(color: fiInk2(context)),
            ),
            FiRows(
              children: [
                FiDataRow(label: 'Na carteira', value: _position(d.stored)),
                FiDataRow(label: 'No razão', value: _position(d.projected)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _Actions extends ConsumerStatefulWidget {
  const _Actions({required this.reconciliation});

  final Reconciliation reconciliation;

  @override
  ConsumerState<_Actions> createState() => _ActionsState();
}

class _ActionsState extends ConsumerState<_Actions> {
  bool _busy = false;

  Future<void> _run(Future<String> Function() acao, String action) async {
    setState(() => _busy = true);
    try {
      final mensagem = await acao();
      if (!mounted) return;
      invalidateLedgerReaders(ref);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(mensagem)));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(fiErrorMessage(e, action: action))),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _backfill() => _run(() async {
    final semeadas = await ref.read(apiRepositoryProvider).backfillLedger();
    return '$semeadas posição(ões) levada(s) para o razão.';
  }, 'levar as posições para o razão');

  Future<void> _rebuild() async {
    final orfas = widget.reconciliation.withoutLedger;
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Refazer a carteira a partir do razão?'),
        content: Text(
          orfas.isEmpty
              ? 'A carteira passa a ser exatamente o que os lançamentos projetam.'
              : 'A carteira passa a ser exatamente o que os lançamentos projetam, e '
                    '${orfas.map((d) => d.ticker).join(', ')} sai da carteira, porque nenhum '
                    'lançamento a sustenta.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Refazer'),
          ),
        ],
      ),
    );
    if (confirmado != true) return;

    await _run(() async {
      final depois = await ref.read(apiRepositoryProvider).rebuildProjection();
      return depois.inSync
          ? 'Carteira refeita: agora ela bate com o razão.'
          : 'Carteira refeita, e ainda restam ${depois.differences.length} diferença(s).';
    }, 'refazer a carteira');
  }

  @override
  Widget build(BuildContext context) {
    final orfas = widget.reconciliation.withoutLedger;

    return FiSection(
      title: 'O que fazer',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (orfas.isNotEmpty) ...[
            Text(
              'Posição sem lançamento sairia da carteira ao refazer. Se ela é sua, leve-a para o '
              'razão antes: cada uma entra como declaração de posição de hoje, com a quantidade '
              'e o preço médio de agora, e a carteira não muda.',
              style: FiType.body.copyWith(color: fiInk2(context)),
            ),
            const SizedBox(height: FiSpace.s3),
            FiButton.primary(
              label: orfas.length == 1
                  ? 'Levar 1 posição para o razão'
                  : 'Levar ${orfas.length} posições para o razão',
              expand: true,
              busy: _busy,
              onPressed: _busy ? null : _backfill,
            ),
            const SizedBox(height: FiSpace.s4),
          ],
          Text(
            'Refazer grava na carteira o que os lançamentos projetam. O razão não muda.',
            style: FiType.body.copyWith(color: fiInk2(context)),
          ),
          const SizedBox(height: FiSpace.s3),
          FiButton(
            label: 'Refazer a carteira a partir do razão',
            tone: orfas.isEmpty ? FiButtonTone.primary : FiButtonTone.secondary,
            expand: true,
            busy: _busy,
            onPressed: _busy ? null : _rebuild,
          ),
        ],
      ),
    );
  }
}
