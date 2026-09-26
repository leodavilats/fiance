import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/score_ruler.dart'
    show
        agreementLabel,
        bandQualityLabel,
        basisLabel,
        confirmationLabel,
        fairBandLabel,
        methodLabel,
        methodStatusLabel,
        principalLabel,
        rateBaseLabel,
        staleRateNote,
        trendBasisLabel;
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/disclosure.dart';
import '../../core/widgets/evidence.dart';
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
import 'buy_sheet.dart';

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
    final nivel = ref.watch(preferencesProvider).valueOrNull?.detailLevel ?? 'completo';

    return analysisFuture.when(
      loading: () => FiSkeleton.screen(
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
        final idade = formatAge(a.asOf);
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
                Flexible(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      FiTag(label: a.label, state: fiVerdictState(a.verdict)),
                      if (basisLabel(a.basis).isNotEmpty) ...[
                        const SizedBox(height: FiSpace.s1),
                        SizedBox(
                          width: 140,
                          child: Text(
                            basisLabel(a.basis),
                            textAlign: TextAlign.end,
                            style: FiType.caption.copyWith(color: fiInk3(context)),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
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
                    note: '${band.label} · faixa de preço justo '
                        '${fairBandLabel(a.fairLow, a.fairHigh)}, '
                        '${confirmationLabel(a.independentInputs)}',
                    state: band.state,
                  );
                },
              ),
            ],

            if (a.reasons.isNotEmpty) ...[
              const SizedBox(height: FiSpace.s5),
              FiEvidence(reasons: a.reasons),
            ],

            if (nivel == 'essencial')
              FiGroupDisclosure(
                label: 'Como chegamos nisso',
                initiallyOpen: false,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: _metodo(context, a),
                ),
              )
            else
              ..._metodo(context, a),

            if (nivel == 'avancado') ..._insumos(context, a),

            if (a.falsifiers.any((f) => f.isPremise))
              FiSection(
                title: 'O que derrubaria a tese',
                hint: 'A premissa que sustenta o preço justo, e a condição que a refuta.',
                child: FiRows(
                  children: [
                    for (final f in a.falsifiers.where((f) => f.isPremise))
                      FiDataRow(label: f.condition),
                  ],
                ),
              ),

            if (a.falsifiers.any((f) => !f.isPremise))
              FiSection(
                title: 'O que muda a classificação',
                hint: 'Atravessar um limiar troca a etiqueta — não refuta a premissa.',
                child: FiRows(
                  children: [
                    for (final f in a.falsifiers.where((f) => !f.isPremise))
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
                  'O preço justo é uma faixa: o método principal da classe, da premissa '
                  'pessimista à otimista. A margem de segurança é a distância do preço de hoje '
                  'até a borda da faixa, e outro insumo confirma ou não a leitura.',
              source: 'Fundamentos e cotações da BRAPI; juro do Banco Central.',
              asOf: idade.isEmpty ? null : 'Preço lido $idade.',
              limitation:
                  'É leitura do sistema sobre dado público, não recomendação de compra.',
            ),

          ],
              ),
            ),
            _BuyFooter(analysis: a),
          ],
        );
      },
    );
  }
}

class _BuyFooter extends ConsumerWidget {
  const _BuyFooter({required this.analysis});

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
              final registrou = await openBuySheet(
                context,
                ref,
                ticker: analysis.symbol,
                currentPrice: analysis.price,
              );
              if (registrou && context.mounted) Navigator.of(context).pop();
            },
          ),
        ),
      ),
    );
  }
}

List<Widget> _metodo(BuildContext context, AssetAnalysis a) => [
    if (a.methods.any((m) => !m.applies && m.status != 'inaplicavel'))
      FiSection(
        title: 'O que ficou de fora, e por quê',
        hint: 'Falta de dado, prejuízo e leitura que não se aplica são silêncios '
            'diferentes.',
        child: FiRows(
          children: [
            for (final m in a.methods.where(
              (m) => !m.applies && m.status != 'inaplicavel',
            ))
              FiDataRow(
                label: methodLabel(m.method),
                detail: methodStatusLabel(m.status),
                note: m.note.isEmpty ? null : m.note,
              ),
          ],
        ),
      ),

    if (a.fairLow != null)
      FiSection(
        title: 'Quanto o ativo vale',
        hint: 'Um método principal, com a faixa das premissas, e outro insumo para '
            'confirmar.',
        child: FiRows(
          children: [
            FiDataRow(
              label: principalLabel(a.principal),
              value: formatCurrency(a.principalValue),
              detail: 'Valor central',
            ),
            FiDataRow(
              label: 'Faixa de preço justo',
              value: fairBandLabel(a.fairLow, a.fairHigh),
              detail: 'Da premissa pessimista à otimista',
              note: a.qualityReasons.isNotEmpty
                  ? a.qualityReasons.join('; ')
                  : bandQualityLabel(a.bandQuality, a.independentInputs),
              emphasis: true,
            ),
            if (a.confirmation != null)
              FiDataRow(
                label: methodLabel(a.confirmation!.method),
                value: formatCurrency(a.confirmation!.value),
                detail: agreementLabel(a.confirmation!.agreement),
              ),
          ],
        ),
      ),

    if (a.premises.isNotEmpty)
      FiSection(
        title: 'As premissas',
        hint: 'O que sustenta a faixa. Se uma delas não se confirmar, a leitura muda.',
        child: FiRows(children: _premiseRows(a)),
      ),

    if (a.indicators.isNotEmpty)
      FiSection(
        title: 'Indicadores que não decidem',
        hint: 'Ajudam a ler o ativo, mas não mexem na faixa.',
        child: FiRows(children: _indicatorRows(a)),
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
            detail: _paceLabel(a.rsi14),
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

    if (FiEvidence.rest(a.reasons).isNotEmpty)
      FiSection(
        title: 'O resto da leitura',
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (final r in FiEvidence.rest(a.reasons))
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
];

List<Widget> _insumos(BuildContext context, AssetAnalysis a) {
  final p = a.premises;
  return [
    FiSection(
      title: 'Os métodos e os insumos',
      hint: 'O nível avançado abre o que o cálculo usou, e por que cada método falou ou calou.',
      child: FiRows(
        children: [
          for (final m in a.methods)
            FiDataRow(
              label: methodLabel(m.method),
              value: m.value == null ? null : formatCurrency(m.value),
              detail: methodStatusLabel(m.status),
              note: m.note.isEmpty ? null : m.note,
            ),
          if (p['reference_date'] != null)
            FiDataRow(
              label: 'Data de referência do cálculo',
              value: formatDate(p['reference_date'] as String?),
            ),
          if (p['selic_pct'] != null)
            FiDataRow(
              label: 'Selic usada',
              value: formatPercent((p['selic_pct'] as num).toDouble()),
              detail: rateBaseLabel(p['rate_base'] as String?),
              note: staleRateNote(p).isEmpty ? null : staleRateNote(p),
            ),
          if (p['fii_segment'] != null)
            FiDataRow(
              label: 'Tipo do fundo',
              value: p['fii_segment'] == 'papel' ? 'Papel' : 'Tijolo ou não classificado',
            ),
        ],
      ),
    ),
  ];
}

final _assetAnalysisProvider = FutureProvider.autoDispose
    .family<AssetAnalysis, String>((ref, ticker) {
      return ref.watch(apiRepositoryProvider).analyzeAsset(ticker);
    });

List<Widget> _premiseRows(AssetAnalysis a) {
  final base = rateBaseLabel(a.premises['rate_base'] as String?);
  final vencida = staleRateNote(a.premises);
  final origemDoYield = [
    if (base.isNotEmpty) 'a partir da $base',
    if (vencida.isNotEmpty) vencida,
  ].join(' · ');

  if (a.principal == 'dividendos') {
    return [
      FiDataRow(
        label: 'Yield exigido',
        value: formatRatio(a.premise('fii_yield')),
        detail: 'Juro real de longo prazo mais prêmio',
        note: origemDoYield.isEmpty ? null : origemDoYield,
      ),
      FiDataRow(
        label: 'Distribuição recorrente',
        value: formatCurrency(a.premise('dividend_recurring')),
        detail: 'Por cota, ao ano',
      ),
    ];
  }

  final payout = a.premise('payout');
  final retido = payout == null ? '' : ' (${formatRatio(1 - payout)})';
  return [
    FiDataRow(
      label: 'Taxa exigida',
      value: formatRatio(a.premise('discount_rate')),
      detail: base.isEmpty ? null : '$base mais 5 pontos',
      note: vencida.isEmpty ? null : vencida,
    ),
    FiDataRow(
      label: 'Crescimento nos próximos 5 anos',
      value: formatRatio(a.premise('growth')),
      detail: 'O ROE de ${formatRatio(a.premise('roe'))} sobre o que a empresa retém$retido',
    ),
    FiDataRow(
      label: 'Crescimento depois',
      value: formatRatio(a.premise('long_run_growth')),
      detail: 'Meta de inflação mais crescimento real',
    ),
    FiDataRow(
      label: 'Lucro por ação normalizado',
      value: formatCurrency(a.premise('eps_normalized')),
      detail: 'Média dos últimos exercícios anuais',
    ),
  ];
}

List<Widget> _indicatorRows(AssetAnalysis a) {
  final graham = a.indicator('graham');
  final teto = a.indicator('preco_teto_pessoal');
  final pvp = a.indicator('pvp');

  return [
    if (teto != null)
      FiDataRow(
        label: 'Preço-teto da sua meta',
        value: formatCurrency(teto.value),
        detail: 'Para render ${formatRatio(teto.desiredYield)} ao ano',
        note: teto.passes == true
            ? 'o preço de hoje cabe na sua meta de renda'
            : 'o preço de hoje não cabe na sua meta de renda',
      ),
    if (graham != null)
      FiDataRow(
        label: 'Critério de Graham',
        value: formatCurrency(graham.value),
        detail: graham.passes == true
            ? 'O preço passa na triagem defensiva'
            : 'O preço não passa na triagem defensiva',
        note: 'é triagem, não preço justo',
      ),
    if (pvp != null)
      FiDataRow(
        label: 'Preço sobre valor patrimonial',
        value: formatQuantity(pvp.value),
        detail: 'P/VP',
      ),
  ];
}

String _paceLabel(double? rsi) {
  if (rsi == null) return 'Sem histórico suficiente';
  if (rsi >= 70) return 'Subiu rápido demais — costuma vir correção';
  if (rsi <= 30) return 'Caiu muito em pouco tempo';
  return 'Sem exagero para nenhum lado';
}
