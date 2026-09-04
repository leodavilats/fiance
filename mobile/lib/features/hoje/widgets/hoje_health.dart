import 'package:flutter/material.dart';

import '../../../core/models.dart';
import '../../../core/theme.dart';

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

String fiHealthBandLabel(double score) {
  if (score >= 70) return 'Bom';
  if (score >= 40) return 'Atenção';
  return 'Ruim';
}

class FiHealthBlock extends StatefulWidget {
  const FiHealthBlock({super.key, required this.health});

  final PortfolioHealth health;

  @override
  State<FiHealthBlock> createState() => _FiHealthBlockState();
}

class _FiHealthBlockState extends State<FiHealthBlock> {
  bool _showInfo = false;

  FiState get _scoreState => fiBandFor(widget.health.score, fiHealthBands).state;

  Color _scoreColor(Brightness brightness) => fiStateColor(_scoreState, brightness);

  @override
  Widget build(BuildContext context) {
    final health = widget.health;
    final brightness = Theme.of(context).brightness;
    final color = _scoreColor(brightness);

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Score geral',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                Row(
                  children: [
                    Text(
                      '${health.score.round()}/100',
                      style: TextStyle(
                        color: color,
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 3,
                      ),
                      decoration: BoxDecoration(
                        color: fiStateSurface(_scoreState, brightness),
                        borderRadius: BorderRadius.circular(999),
                      ),
                      child: Text(
                        fiHealthBandLabel(health.score),
                        style: TextStyle(
                          color: color,
                          fontWeight: FontWeight.w700,
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 12),
            InkWell(
              onTap: () => setState(() => _showInfo = !_showInfo),
              borderRadius: BorderRadius.circular(8),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Expanded(
                      child: _FiHealthMetric(
                        label: 'Concentração',
                        value: health.concentrationScore,
                      ),
                    ),
                    Expanded(
                      child: _FiHealthMetric(
                        label: 'Setor',
                        value: health.sectorConcentrationScore,
                      ),
                    ),
                    Expanded(
                      child: _FiHealthMetric(
                        label: 'Diversif.',
                        value: health.diversificationScore,
                      ),
                    ),
                    Expanded(
                      child: _FiHealthMetric(label: 'Risco', value: health.riskScore),
                    ),
                  ],
                ),
              ),
            ),
            if (_showInfo) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Theme.of(context).dividerColor.withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Wrap(
                        spacing: 12,
                        runSpacing: 4,
                        children: [
                          _FiLegendDot(color: fiStateColor(FiState.favorable, brightness), label: '≥70 bom'),
                          _FiLegendDot(color: fiStateColor(FiState.attention, brightness), label: '40–69 atenção'),
                          _FiLegendDot(color: fiStateColor(FiState.adverse, brightness), label: '<40 ruim'),
                        ],
                      ),
                    ),
                    for (final entry in fiHealthMetricExplanations.entries)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: RichText(
                          text: TextSpan(
                            style: FiType.caption.copyWith(color: fiInk2(context)),
                            children: [
                              TextSpan(
                                text: '${entry.key}: ',
                                style: const TextStyle(fontWeight: FontWeight.w600),
                              ),
                              TextSpan(text: entry.value),
                            ],
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ],
            if (health.warnings.isNotEmpty) ...[
              const SizedBox(height: 12),
              for (final w in health.warnings)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.info_outline, size: 14, color: fiInk2(context)),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          w,
                          style: FiType.caption.copyWith(color: fiInk2(context)),
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _FiLegendDot extends StatelessWidget {
  const _FiLegendDot({required this.color, required this.label});

  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(label, style: TextStyle(color: fiInk2(context), fontSize: 11)),
      ],
    );
  }
}

class _FiHealthMetric extends StatelessWidget {
  const _FiHealthMetric({required this.label, required this.value});

  final String label;
  final double value;

  Color _color(Brightness brightness) {
    if (value >= 70) return fiStateColor(FiState.favorable, brightness);
    if (value >= 40) return fiStateColor(FiState.attention, brightness);
    return fiStateColor(FiState.adverse, brightness);
  }

  @override
  Widget build(BuildContext context) {
    final color = _color(Theme.of(context).brightness);
    return Column(
      children: [
        Text(
          value.round().toString(),
          style: FiType.title.copyWith(color: color),
        ),
        Text(
          label,
          textAlign: TextAlign.center,
          style: TextStyle(color: fiInk2(context), fontSize: 10),
        ),
        Text(
          fiHealthBandLabel(value),
          textAlign: TextAlign.center,
          style: TextStyle(color: color, fontWeight: FontWeight.w600, fontSize: 9),
        ),
      ],
    );
  }
}
