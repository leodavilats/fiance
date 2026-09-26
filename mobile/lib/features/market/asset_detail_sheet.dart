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
import '../../core/product_events.dart';

void showAssetDetailSheet(BuildContext context, String ticker) {
  trackEvent(context, 'first_diagnosis_viewed');
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
                        [
                          assetTypeInWords(a.assetType),
                          translateSector(a.sector),
                        ].where((t) => t.isNotEmpty && t != '—').join(' · '),
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
                    glossaryKey: 'ms',
                    value: pct,
                    min: fiMarginOfSafetyDomain.min,
                    max: fiMarginOfSafetyDomain.max,
                    reference: 0,
                    readout: formatRatio(margem),
                    note: '${band.label}: ${_margemEmPalavras(a)} · '
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
                title: 'O que derrubaria esta leitura',
                hint: 'O que precisa continuar verdade para o preço justo valer. Se deixar de '
                    'ser, a leitura inteira cai.',
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
                hint: 'Se o preço chegar a um destes valores, a etiqueta muda. Isso reclassifica, '
                    'e não derruba a conta.',
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
                  'O preço justo é uma faixa: a conta principal para o tipo de ativo, da premissa '
                  'pessimista à otimista. A margem de segurança é a distância do preço de hoje '
                  'até a borda da faixa, e uma segunda conta, com outro dado, confirma ou não a '
                  'leitura.',
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
                verdict: analysis.verdict,
              );
              if (registrou && context.mounted) Navigator.of(context).pop();
            },
          ),
        ),
      ),
    );
  }
}

const _verbeteDoMetodo = {
  'dcf': 'dcf',
  'bazin': 'bazin',
  'vpa': 'vpa',
  'graham': 'graham',
};

const _qualidade = {
  'firme': 'Firme',
  'ampla': 'Ampla',
  'fragil': 'Frágil',
};

String _margemEmPalavras(AssetAnalysis a) {
  final preco = a.price;
  final piso = a.fairLow;
  final teto = a.fairHigh;
  if (preco == null || piso == null || teto == null) {
    return 'faixa de preço justo ${fairBandLabel(piso, teto)}';
  }
  if (preco < piso) {
    return 'o preço está ${formatCurrency(piso - preco)} abaixo do piso do preço justo, '
        '${formatCurrency(piso)}';
  }
  if (preco > teto) {
    return 'o preço está ${formatCurrency(preco - teto)} acima do teto do preço justo, '
        '${formatCurrency(teto)}';
  }
  return 'o preço está dentro da faixa de preço justo, de ${fairBandLabel(piso, teto)}';
}

List<Widget> _metodo(BuildContext context, AssetAnalysis a) => [
    if (a.methods.any((m) => !m.applies && m.status != 'inaplicavel'))
      FiSection(
        title: 'O que ficou de fora, e por quê',
        hint: 'Cada conta que não entrou diz por quê: faltou dado, a empresa teve prejuízo, ou '
            'a conta não serve para este ativo.',
        child: FiRows(
          children: [
            for (final m in a.methods.where(
              (m) => !m.applies && m.status != 'inaplicavel',
            ))
              FiDataRow(
                label: methodLabel(m.method),
                detail: methodStatusLabel(m.status),
                note: m.note.isEmpty ? null : m.note,
                glossaryKey: _verbeteDoMetodo[m.method],
              ),
          ],
        ),
      ),

    if (a.fairLow != null)
      FiSection(
        title: 'Quanto o ativo vale',
        hint: 'Uma conta principal dá o valor, e as premissas dela dão a faixa. Uma segunda '
            'conta, com outro dado, confirma ou não.',
        child: FiRows(
          children: [
            FiDataRow(
              label: principalLabel(a.principal),
              value: formatCurrency(a.principalValue),
              detail: 'Valor central',
              glossaryKey: a.principal == 'dividendos' ? 'bazin' : 'dcf',
            ),
            FiDataRow(
              label: 'Faixa de preço justo',
              value: fairBandLabel(a.fairLow, a.fairHigh),
              detail: 'Da premissa pessimista à otimista',
              emphasis: true,
              glossaryKey: 'faixa_de_preco_justo',
            ),
            FiDataRow(
              label: 'Quanto confiar na faixa',
              value: _qualidade[a.bandQuality],
              note: a.qualityReasons.isNotEmpty
                  ? a.qualityReasons.join('; ')
                  : bandQualityLabel(a.bandQuality, a.independentInputs),
              glossaryKey: 'qualidade_da_faixa',
            ),
            if (a.confirmation != null)
              FiDataRow(
                label: methodLabel(a.confirmation!.method),
                value: formatCurrency(a.confirmation!.value),
                detail: 'Segunda conta: ${agreementLabel(a.confirmation!.agreement)}',
                glossaryKey: _verbeteDoMetodo[a.confirmation!.method],
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
            glossaryKey: 'tendencia',
          ),
          FiDataRow(
            label: 'Ritmo da alta ou da queda',
            value: a.rsi14?.toStringAsFixed(0) ?? '—',
            detail: _paceLabel(a.rsi14),
            note: a.rsi14 == null ? null : 'Índice de força relativa (RSI), de 0 a 100',
            glossaryKey: 'rsi',
          ),
          if (a.dividendYield != null)
            FiDataRow(
              label: 'Dividendos em 12 meses',
              value: formatRatio(a.dividendYield),
              detail: 'Sobre o preço de hoje',
              glossaryKey: 'dy',
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
      hint: 'O nível avançado abre o que o cálculo usou, e por que cada conta falou ou calou.',
      child: FiRows(
        children: [
          for (final m in a.methods)
            FiDataRow(
              label: methodLabel(m.method),
              value: m.value == null ? null : formatCurrency(m.value),
              detail: methodStatusLabel(m.status),
              note: m.note.isEmpty ? null : m.note,
              glossaryKey: _verbeteDoMetodo[m.method],
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
              glossaryKey: 'selic',
            ),
          if (p['fii_segment'] != null)
            FiDataRow(
              label: 'Tipo do fundo',
              value: p['fii_segment'] == 'papel' ? 'Papel' : 'Tijolo',
              detail: p['fii_segment'] == 'papel'
                  ? 'Vive de dívidas imobiliárias'
                  : 'Tem imóveis, ou não está na lista de fundos de papel',
              glossaryKey: 'fii_de_papel',
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
  final baseComJuro = base.isEmpty ? '' : '$base, o juro básico,';
  final vencida = staleRateNote(a.premises);
  final origemDoYield = [
    if (base.isNotEmpty) 'a partir da $base, o juro básico',
    if (vencida.isNotEmpty) vencida,
  ].join(' · ');

  if (a.principal == 'dividendos') {
    return [
      FiDataRow(
        label: 'Rendimento exigido',
        value: formatRatio(a.premise('fii_yield')),
        detail: 'O juro acima da inflação, no longo prazo, mais um prêmio pelo risco',
        note: origemDoYield.isEmpty ? null : origemDoYield,
        glossaryKey: 'yield',
      ),
      FiDataRow(
        label: 'Distribuição num ano típico',
        value: formatCurrency(a.premise('dividend_recurring')),
        detail: 'Por cota',
        glossaryKey: 'distribuicao_recorrente',
      ),
    ];
  }

  final payout = a.premise('payout');
  final retido = payout == null ? '' : ' (${formatRatio(1 - payout)})';
  return [
    FiDataRow(
      label: 'Taxa exigida',
      value: formatRatio(a.premise('discount_rate')),
      detail: baseComJuro.isEmpty
          ? 'O retorno mínimo, ao ano, para valer a pena'
          : 'O retorno mínimo, ao ano, para valer a pena: $baseComJuro mais 5 pontos',
      note: vencida.isEmpty ? null : vencida,
      glossaryKey: 'taxa_de_desconto',
    ),
    FiDataRow(
      label: 'Crescimento nos próximos 5 anos',
      value: formatRatio(a.premise('growth')),
      detail: 'O retorno sobre o patrimônio (ROE) de ${formatRatio(a.premise('roe'))} vezes a '
          'parte do lucro que a empresa retém$retido',
      glossaryKey: 'roe',
    ),
    FiDataRow(
      label: 'Crescimento depois',
      value: formatRatio(a.premise('long_run_growth')),
      detail: 'A meta de inflação mais um crescimento acima dela',
    ),
    FiDataRow(
      label: 'Lucro por ação, na média',
      value: formatCurrency(a.premise('eps_normalized')),
      detail: 'Média dos últimos anos fechados, para um ano atípico não pesar demais',
      glossaryKey: 'lpa',
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
        detail: 'Para render ${formatRatio(teto.desiredYield)} ao ano em proventos',
        note: teto.passes == true
            ? 'o preço de hoje cabe na sua meta de renda'
            : 'o preço de hoje não cabe na sua meta de renda',
        glossaryKey: 'preco_teto_pessoal',
      ),
    if (graham != null)
      FiDataRow(
        label: 'Critério de Graham',
        value: formatCurrency(graham.value),
        detail: graham.passes == true
            ? 'O preço passa no filtro de Graham para o investidor defensivo'
            : 'O preço não passa no filtro de Graham para o investidor defensivo',
        note: 'é filtro, não preço justo',
        glossaryKey: 'graham',
      ),
    if (pvp != null)
      FiDataRow(
        label: 'Preço sobre valor patrimonial',
        value: formatQuantity(pvp.value),
        detail: 'P/VP: quanto se paga por R\$ 1 do patrimônio que está no balanço',
        glossaryKey: 'pvp',
      ),
  ];
}

String _paceLabel(double? rsi) {
  if (rsi == null) return 'Sem histórico suficiente';
  if (rsi >= 70) return 'Subiu rápido em pouco tempo';
  if (rsi <= 30) return 'Caiu rápido em pouco tempo';
  return 'Sem exagero para nenhum lado';
}
