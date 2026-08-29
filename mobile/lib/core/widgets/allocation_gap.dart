import 'package:flutter/material.dart';

import '../theme.dart';

/// A terceira leitura da régua: **onde estou diferente do que planejei**.
///
/// Espelha `AllocationGapComponent` no web — mesma mecânica, mesmas bandas
/// (`fiAllocationGapBands`, de `design-tokens/tokens.json`), mesma regra: a
/// barra é a alocação atual, o fio é a meta, e quem ganha estado é a distância
/// entre as duas, não o tamanho da barra.
///
/// Desvio não é perda: o pior estado possível aqui é "atenção". E sem meta
/// definida não há julgamento nenhum — comparar contra uma meta que não existe
/// seria inventar o número.
class FiAllocationGap extends StatelessWidget {
  const FiAllocationGap({
    super.key,
    required this.label,
    required this.currentPct,
    this.targetPct,
    this.barColor,
    this.trailing,
  });

  final String label;
  final double currentPct;
  final double? targetPct;
  final Color? barColor;

  /// Texto à direita — normalmente o valor em reais.
  final String? trailing;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final hasTarget = targetPct != null;
    final delta = hasTarget ? currentPct - targetPct! : 0.0;
    final band = fiBandFor(delta.abs(), fiAllocationGapBands, hasTarget ? 1 : 0);
    final stateColor = fiStateColor(band.state, brightness);
    final brand = Theme.of(context).colorScheme.primary;

    return Semantics(
      label: hasTarget
          ? '$label: ${currentPct.toStringAsFixed(1)}% da carteira contra meta de '
                '${targetPct!.toStringAsFixed(1)}% — ${delta.abs().toStringAsFixed(1)} pontos '
                'percentuais ${delta > 0 ? 'acima' : 'abaixo'}, ${band.label.toLowerCase()}'
          : '$label: ${currentPct.toStringAsFixed(1)}% da carteira, sem meta definida',
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: Text(label)),
                if (trailing != null) ...[
                  Text(
                    trailing!,
                    style: FiType.caption.copyWith(color: fiInk2(context)),
                  ),
                  const SizedBox(width: 8),
                ],
                SizedBox(
                  width: 52,
                  child: Text(
                    '${currentPct.toStringAsFixed(1)}%',
                    textAlign: TextAlign.right,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            LayoutBuilder(
              builder: (context, constraints) {
                final width = constraints.maxWidth;
                final fill = (currentPct.clamp(0, 100) / 100) * width;
                final tick = hasTarget
                    ? (targetPct!.clamp(0, 100) / 100) * width
                    : null;
                return SizedBox(
                  height: 12,
                  child: Stack(
                    children: [
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Container(
                          height: 8,
                          width: width,
                          decoration: BoxDecoration(
                            color: Theme.of(context).colorScheme.surfaceContainerHighest,
                            borderRadius: BorderRadius.circular(FiRadius.sm),
                          ),
                        ),
                      ),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Container(
                          height: 8,
                          width: fill,
                          decoration: BoxDecoration(
                            color: barColor ?? fiInk3(context),
                            borderRadius: BorderRadius.circular(FiRadius.sm),
                          ),
                        ),
                      ),
                      if (tick != null)
                        Positioned(
                          left: (tick - 1).clamp(0, width - 2),
                          top: 0,
                          bottom: 0,
                          child: Container(width: 2, color: brand),
                        ),
                    ],
                  ),
                );
              },
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                if (hasTarget) ...[
                  Text(
                    'meta ${targetPct!.toStringAsFixed(0)}%',
                    style: TextStyle(color: fiInk3(context), fontSize: 11),
                  ),
                  const Spacer(),
                  Icon(
                    delta.abs() < 1
                        ? Icons.drag_handle
                        : (delta > 0 ? Icons.arrow_upward : Icons.arrow_downward),
                    size: 12,
                    color: stateColor,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    '${delta > 0 ? '+' : ''}${delta.toStringAsFixed(1)} p.p.',
                    style: TextStyle(
                      color: stateColor,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ] else
                  Text(
                    'sem meta definida',
                    style: TextStyle(
                      color: fiStateColor(FiState.indeterminate, brightness),
                      fontSize: 11,
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
