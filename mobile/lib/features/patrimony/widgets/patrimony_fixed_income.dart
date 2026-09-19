import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/format.dart';
import '../../../core/labels.dart';
import '../../../core/models.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/data_row.dart';
import '../../../core/widgets/disclosure.dart';
import '../../../core/widgets/error_state.dart';
import '../../../core/widgets/nav_action.dart';
import '../../../core/widgets/section.dart';
import '../../../core/widgets/skeleton.dart';

class FiFixedIncomeSection extends ConsumerWidget {
  const FiFixedIncomeSection({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final fixedIncome = ref.watch(fixedIncomeProvider);

    return fixedIncome.when(
      loading: () => const FiSection(
        title: 'Renda fixa',
        child: FiSkeleton(shape: FiSkeletonShape.row, count: 2),
      ),
      error: (err, _) => FiSection(
        title: 'Renda fixa',
        child: FiErrorState(
          error: err,
          action: 'carregar suas aplicações de renda fixa',
          onRetry: () => ref.invalidate(fixedIncomeProvider),
        ),
      ),
      data: (data) {
        final visible = data.visible;
        if (visible.isEmpty) return const SizedBox.shrink();

        final brightness = Theme.of(context).brightness;
        final rendeu = data.totalReturn >= 0;
        final vencendo = visible.where((i) => i.maturingSoon).toList();
        final ordenadas = [...visible]
          ..sort((a, b) => b.currentValue.compareTo(a.currentValue));

        return FiSection(
          title: 'Renda fixa',
          count: visible.length,
          action: FiNavAction(
            label: 'Gerenciar aplicações',
            onPressed: () => context.go('/patrimonio/renda-fixa'),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              FiFigures(
                rule: false,
                figures: {
                  'HOJE': formatCurrency(data.totalCurrent),
                  'APLICADO': formatCurrency(data.totalInvested),
                },
              ),
              const SizedBox(height: FiSpace.s2),
              Text(
                '${rendeu ? '+' : ''}${formatCurrency(data.totalReturn)} '
                '(${formatPercent(data.returnPct)}) de rendimento sobre o aplicado.',
                style: FiType.caption.copyWith(
                  color: fiDirectionColor(rendeu ? 1 : -1, brightness),
                ),
              ),
              if (vencendo.isNotEmpty) ...[
                const SizedBox(height: FiSpace.s1),
                Text(
                  vencendo.length == 1
                      ? '${vencendo.first.name} vence nos próximos 30 dias — planeje a '
                            'reaplicação antes.'
                      : '${vencendo.length} aplicações vencem nos próximos 30 dias — '
                            'planeje a reaplicação antes.',
                  style: FiType.caption.copyWith(
                    color: fiStateColor(FiState.attention, brightness),
                  ),
                ),
              ],
              const SizedBox(height: FiSpace.s4),
              for (final item in ordenadas) _HoldingDisclosure(item: item),
            ],
          ),
        );
      },
    );
  }
}

class _HoldingDisclosure extends StatelessWidget {
  const _HoldingDisclosure({required this.item});

  final FixedIncomePosition item;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final rendeu = item.accruedReturn >= 0;

    return FiDisclosure(
      title: item.name,
      value: formatCurrency(item.currentValue),
      detail: item.maturingSoon
          ? '${fixedIncomeKindLabel(item.kind)} · vence em '
                '${item.daysToMaturity} dias'
          : '${fixedIncomeKindLabel(item.kind)} · '
                '${rendeu ? '+' : ''}${formatPercent(item.returnPct)}',
      child: FiRows(
        children: [
          FiDataRow(
            label: 'Aplicado',
            value: formatCurrency(item.investedValue),
          ),
          FiDataRow(
            label: 'Rendimento',
            value:
                '${rendeu ? '+' : ''}${formatCurrency(item.accruedReturn)}',
            detail: '${rendeu ? '+' : ''}${formatPercent(item.returnPct)} '
                'sobre o aplicado',
            valueColor: fiDirectionColor(rendeu ? 1 : -1, brightness),
            emphasis: true,
          ),
          FiDataRow(
            label: 'Taxa',
            value: item.cdiPercent != null
                ? '${formatPercent(item.cdiPercent)} do CDI'
                : '${formatPercent(item.rate)} ao ano',
            detail: '${formatPercent(item.effectiveAnnualRatePct)} ao ano na prática',
          ),
          FiDataRow(
            label: 'Vencimento',
            value: item.maturity == null
                ? fixedIncomeLiquidityLabel(item.liquidity)
                : formatDate(item.maturity),
            detail: item.daysToMaturity == null
                ? null
                : 'em ${item.daysToMaturity} dias',
            valueColor: item.maturingSoon
                ? fiStateColor(FiState.attention, brightness)
                : null,
          ),
          if (item.irExempt == true)
            const FiDataRow(label: 'IR', value: 'Isento'),
        ],
      ),
    );
  }
}
