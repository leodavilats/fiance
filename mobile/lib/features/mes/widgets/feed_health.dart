import 'package:flutter/material.dart';

import '../../../core/models.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/button.dart';
import '../../../core/widgets/measure.dart';
import '../../../core/widgets/score_ruler.dart';
import '../../../core/widgets/provenance.dart';

const fiHealthMetricExplanations = {
  'Concentração':
      'O quanto seu maior ativo pesa na carteira. Nota boa = nenhum ativo domina muito o total; nota ruim = um único papel concentra boa parte do patrimônio.',
  'Setor':
      'O quanto suas ações/BDRs dependem de um único setor da economia. Nota boa = exposição espalhada entre setores; nota ruim = carteira muito presa a um setor só.',
  'Diversificação':
      'A variedade entre categorias (renda fixa, ações BR, BDRs, FIIs, ETFs) e o número de ativos. Nota boa = carteira cobrindo várias categorias; nota ruim = tudo concentrado em 1-2 categorias.',
  'Risco':
      'A fatia da carteira em ativos com sinal de venda hoje. Nota boa = pouca ou nenhuma exposição a esses ativos; nota ruim = parte relevante da carteira pede atenção.',
};

// A DIMENSAO tem regua propria: e outro numero -- 0-100 por eixo (concentracao, setor,
// diversificacao, risco), nao o score de saude -- e o backend nao devolve faixa para ela.
// O score de SAUDE nao passa por aqui: ele le `fiHealthBands`.
const List<FiScoreBand> fiHealthDimensionBands = [
  FiScoreBand(
    id: 'good',
    min: 70,
    max: 100,
    label: 'Bom',
    state: FiState.favorable,
    emphasis: 'muted',
  ),
  FiScoreBand(
    id: 'watch',
    min: 40,
    max: 69,
    label: 'Atenção',
    state: FiState.attention,
    emphasis: 'muted',
  ),
  FiScoreBand(
    id: 'poor',
    min: 0,
    max: 39,
    label: 'Ruim',
    state: FiState.adverse,
    emphasis: 'strong',
  ),
];

String fiDimensionBandLabel(double value) =>
    fiBandFor(value, fiHealthDimensionBands).label;

class FiHealthBlock extends StatefulWidget {
  const FiHealthBlock({super.key, required this.health});

  final PortfolioHealth health;

  @override
  State<FiHealthBlock> createState() => _FiHealthBlockState();
}

class _FiHealthBlockState extends State<FiHealthBlock> {
  bool _showInfo = false;

  @override
  Widget build(BuildContext context) {
    final health = widget.health;

    final dimensoes = <String, double>{
      'Concentração': health.concentrationScore,
      'Setor': health.sectorConcentrationScore,
      'Diversificação': health.diversificationScore,
      'Risco': health.riskScore,
    };

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ScoreRuler(
          score: health.score,
          bands: fiHealthBands,
          size: ScoreRulerSize.card,
          subject: 'Saúde da carteira',
        ),

        const SizedBox(height: FiSpace.s5),
        for (final entry in dimensoes.entries)
          Builder(
            builder: (context) {
              final band = fiBandFor(entry.value, fiHealthDimensionBands);
              return FiMeasure(
                label: entry.key,
                value: entry.value,
                readout: entry.value.round().toString(),
                note: band.label,
                state: band.state,
              );
            },
          ),

        if (_showInfo) ...[
          const SizedBox(height: FiSpace.s4),
          Text(
            'Cada dimensão vai de 0 a 100: 70 ou mais é bom, de 40 a 69 pede atenção, abaixo '
            'de 40 é ruim.',
            style: FiType.caption.copyWith(color: fiInk3(context)),
          ),
          const SizedBox(height: FiSpace.s3),
          for (final entry in fiHealthMetricExplanations.entries)
            Padding(
              padding: const EdgeInsets.only(bottom: FiSpace.s3),
              child: RichText(
                text: TextSpan(
                  style: FiType.caption.copyWith(color: fiInk2(context)),
                  children: [
                    TextSpan(
                      text: '${entry.key} — ',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    TextSpan(text: entry.value),
                  ],
                ),
              ),
            ),
        ],

        Align(
          alignment: Alignment.centerLeft,
          child: FiButton.quiet(
            label: _showInfo
                ? 'Recolher o que cada dimensão mede'
                : 'O que cada dimensão mede',
            onPressed: () => setState(() => _showInfo = !_showInfo),
          ),
        ),

        if (health.warnings.isNotEmpty) ...[
          const SizedBox(height: FiSpace.s3),
          for (final w in health.warnings)
            Padding(
              padding: const EdgeInsets.only(bottom: FiSpace.s2),
              child: Text(
                w,
                style: FiType.caption.copyWith(
                  color: fiStateColor(
                    FiState.attention,
                    Theme.of(context).brightness,
                  ),
                ),
              ),
            ),
        ],

        FiProvenance(
          summary: 'Como lemos a saúde da carteira',
          method:
              'Quatro dimensões em 0-100 — concentração, setor, diversificação e risco — '
              'combinadas num score, lido na régua de saúde do sistema.',
          source: 'Suas posições e renda fixa, com preços da BRAPI.',
          limitation:
              'Com menos de quatro ativos concentração e diversificação não dizem muito, '
              'e a leitura sai como carteira pequena demais para avaliar.',
        ),
      ],
    );
  }
}
