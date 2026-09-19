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
    final rendaFixa = ref.watch(fixedIncomeProvider);

    return rendaFixa.when(
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
        final visiveis = data.visiveis;
        if (visiveis.isEmpty) return const SizedBox.shrink();

        final brightness = Theme.of(context).brightness;
        final rendeu = data.totalRendimento >= 0;
        final vencendo = visiveis.where((i) => i.vencimentoProximo).toList();
        final ordenadas = [...visiveis]
          ..sort((a, b) => b.valorAtual.compareTo(a.valorAtual));

        return FiSection(
          title: 'Renda fixa',
          count: visiveis.length,
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
                  'HOJE': formatCurrency(data.totalAtual),
                  'APLICADO': formatCurrency(data.totalInvestido),
                },
              ),
              const SizedBox(height: FiSpace.s2),
              Text(
                '${rendeu ? '+' : ''}${formatCurrency(data.totalRendimento)} '
                '(${formatPercent(data.rendimentoPct)}) de rendimento sobre o aplicado.',
                style: FiType.caption.copyWith(
                  color: fiDirectionColor(rendeu ? 1 : -1, brightness),
                ),
              ),
              if (vencendo.isNotEmpty) ...[
                const SizedBox(height: FiSpace.s1),
                Text(
                  vencendo.length == 1
                      ? '${vencendo.first.nome} vence nos próximos 30 dias — planeje a '
                            'reaplicação antes.'
                      : '${vencendo.length} aplicações vencem nos próximos 30 dias — '
                            'planeje a reaplicação antes.',
                  style: FiType.caption.copyWith(
                    color: fiStateColor(FiState.attention, brightness),
                  ),
                ),
              ],
              const SizedBox(height: FiSpace.s4),
              for (final item in ordenadas) _AplicacaoExpansivel(item: item),
            ],
          ),
        );
      },
    );
  }
}

class _AplicacaoExpansivel extends StatelessWidget {
  const _AplicacaoExpansivel({required this.item});

  final FixedIncomePosition item;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final rendeu = item.rendimentoAcumulado >= 0;

    return FiDisclosure(
      title: item.nome,
      value: formatCurrency(item.valorAtual),
      detail: item.vencimentoProximo
          ? '${rendaFixaTipoLabel(item.tipo)} · vence em '
                '${item.diasParaVencimento} dias'
          : '${rendaFixaTipoLabel(item.tipo)} · '
                '${rendeu ? '+' : ''}${formatPercent(item.rendimentoPct)}',
      child: FiRows(
        children: [
          FiDataRow(
            label: 'Aplicado',
            value: formatCurrency(item.valorInvestido),
          ),
          FiDataRow(
            label: 'Rendimento',
            value:
                '${rendeu ? '+' : ''}${formatCurrency(item.rendimentoAcumulado)}',
            detail: '${rendeu ? '+' : ''}${formatPercent(item.rendimentoPct)} '
                'sobre o aplicado',
            valueColor: fiDirectionColor(rendeu ? 1 : -1, brightness),
            emphasis: true,
          ),
          FiDataRow(
            label: 'Taxa',
            value: item.percentualCdi != null
                ? '${formatPercent(item.percentualCdi)} do CDI'
                : '${formatPercent(item.taxa)} ao ano',
            detail: '${formatPercent(item.taxaAnualEfetivaPct)} ao ano na prática',
          ),
          FiDataRow(
            label: 'Vencimento',
            value: item.vencimento == null
                ? liquidezLabel(item.liquidez)
                : formatDate(item.vencimento),
            detail: item.diasParaVencimento == null
                ? null
                : 'em ${item.diasParaVencimento} dias',
            valueColor: item.vencimentoProximo
                ? fiStateColor(FiState.attention, brightness)
                : null,
          ),
          if (item.isentoIr == true)
            const FiDataRow(label: 'IR', value: 'Isento'),
        ],
      ),
    );
  }
}
