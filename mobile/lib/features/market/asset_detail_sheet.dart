import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

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
import 'comprar_sheet.dart';

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

        return Column(
          children: [
            Expanded(
              child: ListView(
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
              title: 'Quanto o ativo vale, por cada método',
              hint: 'Cada método olha para uma coisa diferente. Quando eles concordam, a '
                  'estimativa é mais firme.',
              child: FiRows(
                children: [
                  if (a.bazin != null)
                    FiDataRow(
                      label: 'Pelos dividendos que paga',
                      value: formatCurrency(a.bazin),
                      detail: 'Método Bazin',
                      note: dataYearsLabel(a.dataYears),
                    ),
                  if (a.graham != null)
                    FiDataRow(
                      label: 'Pelo lucro e pelo patrimônio',
                      value: formatCurrency(a.graham),
                      detail: 'Fórmula de Graham',
                    ),
                  FiDataRow(
                    label: 'Preço justo estimado',
                    value: formatCurrency(a.consensus),
                    note: consensusLabel(a.consensusMethods),
                    emphasis: true,
                  ),
                ],
              ),
            ),

            FiSection(
              title: 'O que o preço vem fazendo',
              hint: 'Isto não diz se a empresa é boa: diz por onde o preço tem andado.',
              child: FiRows(
                children: [
                  FiDataRow(
                    label: 'Direção recente',
                    value: trendLabel(a.trend),
                    note: trendBasisLabel(a.trendBasis),
                  ),
                  FiDataRow(
                    label: 'Ritmo da alta ou da queda',
                    value: a.rsi14?.toStringAsFixed(0) ?? '—',
                    detail: _ritmoLabel(a.rsi14),
                  ),
                  if (a.dividendYield != null)
                    FiDataRow(
                      label: 'Dividendos em 12 meses',
                      value: formatRatio(a.dividendYield),
                      detail: 'Sobre o preço de hoje',
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

          ],
              ),
            ),
            _RodapeDeCompra(analysis: a),
          ],
        );
      },
    );
  }
}

class _RodapeDeCompra extends ConsumerWidget {
  const _RodapeDeCompra({required this.analysis});

  final AssetAnalysis analysis;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final brightness = Theme.of(context).brightness;

    return Container(
      decoration: BoxDecoration(
        color: fiGround1(brightness),
        border: Border(top: BorderSide(color: fiHairline(brightness))),
      ),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(
            FiSpace.s5,
            FiSpace.s3,
            FiSpace.s5,
            FiSpace.s3,
          ),
          child: FiButton.primary(
            label: 'Já comprei este ativo',
            icon: Icons.add,
            expand: true,
            onPressed: () async {
              final registrou = await abrirCompraDeAtivo(
                context,
                ref,
                ticker: analysis.symbol,
                precoAtual: analysis.price,
              );
              if (registrou && context.mounted) Navigator.of(context).pop();
            },
          ),
        ),
      ),
    );
  }
}

final _assetAnalysisProvider = FutureProvider.autoDispose
    .family<AssetAnalysis, String>((ref, ticker) {
      return ref.watch(apiRepositoryProvider).analyzeAsset(ticker);
    });

String _ritmoLabel(double? rsi) {
  if (rsi == null) return 'Sem histórico suficiente';
  if (rsi >= 70) return 'Subiu rápido demais — costuma vir correção';
  if (rsi <= 30) return 'Caiu muito em pouco tempo';
  return 'Sem exagero para nenhum lado';
}
