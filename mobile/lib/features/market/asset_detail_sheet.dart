import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/score_ruler.dart' show consensusLabel, dataYearsLabel, trendBasisLabel;
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/measure.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/sector_translations.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';

void showAssetDetailSheet(BuildContext context, String ticker) {
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (context) => DraggableScrollableSheet(
      initialChildSize: 0.75,
      minChildSize: 0.4,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollController) => _AssetDetailContent(
        ticker: ticker,
        scrollController: scrollController,
      ),
    ),
  );
}

class _AssetDetailContent extends ConsumerWidget {
  const _AssetDetailContent({
    required this.ticker,
    required this.scrollController,
  });

  final String ticker;
  final ScrollController scrollController;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analysisFuture = ref.watch(_assetAnalysisProvider(ticker));

    return analysisFuture.when(
      loading: () => FiSkeleton.tela(
        shape: FiSkeletonShape.verdict,
        count: 1,
        label: 'Analisando este ativo',
      ),
      error: (err, _) => FiErrorState(
        error: err,
        action: 'analisar $ticker',
        onRetry: () => ref.invalidate(_assetAnalysisProvider(ticker)),
      ),
      data: (a) {
        final idade = formatIdade(a.asOf);
        final margem = a.marginOfSafety;

        return ListView(
          controller: scrollController,
          padding: const EdgeInsets.fromLTRB(
            FiSpace.s5,
            0,
            FiSpace.s5,
            FiSpace.s8,
          ),
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        a.symbol,
                        style: FiType.pageTitle.copyWith(color: fiInk1(context)),
                      ),
                      if (a.name != null)
                        Text(
                          a.name!,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: FiType.body.copyWith(color: fiInk2(context)),
                        ),
                      Text(
                        translateSector(a.sector),
                        style: FiType.caption.copyWith(color: fiInk3(context)),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: FiSpace.s3),
                FiTag(label: a.label, state: fiVerdictState(a.verdict)),
              ],
            ),

            const SizedBox(height: FiSpace.s5),
            FiHeadline(
              eyebrow: 'Preço',
              figure: formatCurrency(a.price),
              note: idade.isEmpty ? null : 'lido $idade',
            ),

            if (margem != null) ...[
              const SizedBox(height: FiSpace.s5),
              Builder(
                builder: (context) {
                  final pct = margem * 100;
                  final band = fiBandFor(pct, fiMarginOfSafetyBands);
                  return FiMeasure(
                    label: 'Margem de segurança',
                    value: pct,
                    min: fiMarginOfSafetyDomain.min,
                    max: fiMarginOfSafetyDomain.max,
                    reference: 0,
                    readout: formatRatio(margem),
                    note: '${band.label} · preço justo ${formatCurrency(a.consensus)}, '
                        '${consensusLabel(a.consensusMethods)}',
                    state: band.state,
                  );
                },
              ),
            ],

            FiSection(
              title: 'A conta por trás do preço justo',
              child: FiRows(
                children: [
                  if (a.bazin != null)
                    FiDataRow(
                      label: 'Bazin',
                      value: formatCurrency(a.bazin),
                      note: dataYearsLabel(a.dataYears),
                    ),
                  if (a.graham != null)
                    FiDataRow(label: 'Graham', value: formatCurrency(a.graham)),
                  FiDataRow(
                    label: 'Consenso',
                    value: formatCurrency(a.consensus),
                    note: consensusLabel(a.consensusMethods),
                    emphasis: true,
                  ),
                ],
              ),
            ),

            FiSection(
              title: 'O técnico',
              child: FiRows(
                children: [
                  FiDataRow(
                    label: 'Tendência',
                    value: trendLabel(a.trend),
                    note: trendBasisLabel(a.trendBasis),
                  ),
                  FiDataRow(
                    label: 'Força relativa (RSI 14)',
                    value: a.rsi14?.toStringAsFixed(1) ?? '—',
                  ),
                ],
              ),
            ),

            if (a.reasons.isNotEmpty)
              FiSection(
                title: 'Por que esta leitura',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    for (final r in a.reasons)
                      Padding(
                        padding: const EdgeInsets.only(bottom: FiSpace.s3),
                        child: Text(
                          r,
                          style: FiType.body.copyWith(color: fiInk2(context)),
                        ),
                      ),
                  ],
                ),
              ),

            if (a.falsifiers.isNotEmpty)
              FiSection(
                title: 'O que derrubaria a leitura',
                hint: 'A condição conferível em que o veredito muda.',
                child: FiRows(
                  children: [
                    for (final f in a.falsifiers)
                      FiDataRow(
                        label: f.condition,
                        detail: 'passa a ${f.becomesLabel}',
                      ),
                  ],
                ),
              ),

            const SizedBox(height: FiSpace.s4),
            FiProvenance(
              summary: 'Como chegamos nesta leitura',
              method:
                  'O preço justo é o consenso dos métodos aplicáveis ao papel; a margem de '
                  'segurança é a distância entre o preço de hoje e esse consenso.',
              source: 'Fundamentos e cotações da BRAPI.',
              asOf: idade.isEmpty ? null : 'Preço lido $idade.',
              limitation:
                  'É leitura do sistema sobre dado público, não recomendação de compra.',
            ),

            const SizedBox(height: FiSpace.s5),
            FiButton.secondary(
              label: 'Abrir a análise completa',
              expand: true,
              onPressed: () {
                Navigator.of(context).pop();
                context.push('/ativo/${a.symbol}');
              },
            ),
          ],
        );
      },
    );
  }
}

final _assetAnalysisProvider = FutureProvider.autoDispose
    .family<AssetAnalysis, String>((ref, ticker) {
      return ref.watch(apiRepositoryProvider).analyzeAsset(ticker);
    });
