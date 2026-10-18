import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/ledger_models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/feedback.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';

const _reasons = {
  'no_razao_sem_posicao': 'Os lançamentos têm esta posição aberta, e a carteira não a mostra.',
  'posicao_sem_razao': 'A carteira tem esta posição, e nenhum lançamento a sustenta.',
  'quantidade': 'A quantidade da carteira difere da que os lançamentos dão.',
  'preco_medio': 'O preço médio da carteira difere do que os lançamentos dão.',
};

class ReconciliationScreen extends ConsumerWidget {
  const ReconciliationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final conferencia = ref.watch(reconciliationProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Conferir as posições')),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(reconciliationProvider),
        child: conferencia.when(
          loading: () => FiSkeleton.screen(
            shape: FiSkeletonShape.row,
            count: 4,
            label: 'Conferindo a carteira contra os lançamentos',
          ),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos conferir a carteira',
            action: 'conferir a carteira contra os lançamentos',
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
                    ? 'A carteira bate com os lançamentos'
                    : data.differences.length == 1
                    ? '1 diferença entre a carteira e os lançamentos'
                    : '${data.differences.length} diferenças entre a carteira e os lançamentos',
                style: FiType.title.copyWith(color: fiInk1(context)),
              ),
              const SizedBox(height: FiSpace.s2),
              Text(
                data.inSync
                    ? data.positions == 1
                          ? '1 posição na carteira, e ela é exatamente o que os lançamentos '
                                'dão.'
                          : '${data.positions} posições na carteira, e cada uma é exatamente o '
                                'que os lançamentos dão.'
                    : 'A carteira deveria ser só a soma dos lançamentos. Onde ela diverge, valem '
                          'os lançamentos — a menos que falte lançar alguma coisa.',
                style: FiType.body.copyWith(color: fiInk2(context)),
              ),
              const SizedBox(height: FiSpace.s2),
              const FiProvenance(
                summary: 'Como a conferência é feita',
                method: 'Cada lançamento é reaplicado em ordem, pela convenção brasileira '
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
                FiDataRow(label: 'Nos lançamentos', value: _position(d.projected)),
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
    String? mensagem;
    final ok = await fiAttempt(context, () async {
      mensagem = await acao();
    }, action: action);
    if (!mounted) return;
    final texto = mensagem;
    if (ok && texto != null) {
      invalidateLedgerReaders(ref);
      fiNotify(context, texto);
    }
    setState(() => _busy = false);
  }

  Future<void> _backfill() => _run(() async {
    final semeadas = await ref.read(apiRepositoryProvider).backfillLedger();
    return semeadas == 1
        ? '1 posição levada para os lançamentos.'
        : '$semeadas posições levadas para os lançamentos.';
  }, 'levar as posições para os lançamentos');

  Future<void> _rebuild() async {
    final orfas = widget.reconciliation.withoutLedger;
    final confirmado = await fiConfirm(
      context,
      title: 'Refazer a carteira a partir dos lançamentos?',
      body: orfas.isEmpty
          ? 'A carteira passa a ser exatamente o que os lançamentos dão.'
          : 'A carteira passa a ser exatamente o que os lançamentos dão, e '
                '${orfas.map((d) => d.ticker).join(', ')} sai da carteira, porque nenhum '
                'lançamento a sustenta.',
      confirmLabel: 'Refazer',
    );
    if (!confirmado || !mounted) return;

    await _run(() async {
      final depois = await ref.read(apiRepositoryProvider).rebuildProjection();
      return depois.inSync
          ? 'Carteira refeita: agora ela bate com os lançamentos.'
          : depois.differences.length == 1
          ? 'Carteira refeita, e ainda resta 1 diferença.'
          : 'Carteira refeita, e ainda restam ${depois.differences.length} diferenças.';
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
              'Posição sem lançamento sairia da carteira ao refazer. Se ela é sua, leve-a para os '
              'lançamentos antes: cada uma entra como declaração de posição de hoje, com a quantidade '
              'e o preço médio de agora, e a carteira não muda.',
              style: FiType.body.copyWith(color: fiInk2(context)),
            ),
            const SizedBox(height: FiSpace.s3),
            FiButton.primary(
              label: orfas.length == 1
                  ? 'Levar 1 posição para os lançamentos'
                  : 'Levar ${orfas.length} posições para os lançamentos',
              expand: true,
              busy: _busy,
              onPressed: _busy ? null : _backfill,
            ),
            const SizedBox(height: FiSpace.s4),
          ],
          Text(
            'Refazer grava na carteira o que os lançamentos dão. Os lançamentos não mudam.',
            style: FiType.body.copyWith(color: fiInk2(context)),
          ),
          const SizedBox(height: FiSpace.s3),
          FiButton(
            label: 'Refazer a carteira a partir dos lançamentos',
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
