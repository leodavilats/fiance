import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/format.dart';
import '../../../core/labels.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/button.dart';
import '../../../core/widgets/data_row.dart';
import '../../../core/widgets/section.dart';

const _mesesAbreviados = [
  'jan',
  'fev',
  'mar',
  'abr',
  'mai',
  'jun',
  'jul',
  'ago',
  'set',
  'out',
  'nov',
  'dez',
];

String _mesPorExtenso(String mes) {
  final partes = mes.split('-');
  if (partes.length != 2) return mes;
  final numero = int.tryParse(partes[1]);
  if (numero == null || numero < 1 || numero > 12) return mes;
  return '${_mesesAbreviados[numero - 1]}/${partes[0]}';
}

class FiClosedTradesSection extends ConsumerStatefulWidget {
  const FiClosedTradesSection({super.key});

  @override
  ConsumerState<FiClosedTradesSection> createState() =>
      _FiClosedTradesSectionState();
}

class _FiClosedTradesSectionState extends ConsumerState<FiClosedTradesSection> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final trades = ref.watch(closedTradesProvider);

    return trades.when(
      loading: () => const SizedBox.shrink(),
      error: (_, _) => const SizedBox.shrink(),
      data: (data) {
        if (data.trades.isEmpty) return const SizedBox.shrink();

        final brightness = Theme.of(context).brightness;
        final totalColor = fiDirectionColor(
          data.totalRealizedPnl >= 0 ? 1 : -1,
          brightness,
        );

        return FiSection(
          title: 'Operações encerradas',
          count: data.trades.length,
          action: FiButton.quiet(
            label: _expanded ? 'Recolher o detalhe' : 'Ver apuração e vendas',
            onPressed: () => setState(() => _expanded = !_expanded),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              FiFigures(
                rule: false,
                figures: {
                  'RESULTADO REALIZADO': formatCurrency(data.totalRealizedPnl),
                  'IR APURADO': formatCurrency(data.totalIrPaid),
                },
              ),
              const SizedBox(height: FiSpace.s2),
              Text(
                'O resultado realizado soma o que saiu da carteira; '
                '${data.totalRealizedPnl >= 0 ? 'está positivo' : 'está negativo'} no período.',
                style: FiType.caption.copyWith(color: totalColor),
              ),

              if (_expanded) ...[
                if (data.months.isNotEmpty) ...[
                  const SizedBox(height: FiSpace.s6),
                  Text(
                    'APURAÇÃO POR MÊS',
                    style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                  ),
                  const SizedBox(height: FiSpace.s1),
                  Text(
                    'O imposto é do mês, não da venda: lucros e prejuízos do mesmo mês e da '
                    'mesma categoria se compensam.',
                    style: FiType.caption.copyWith(color: fiInk2(context)),
                  ),
                  const SizedBox(height: FiSpace.s3),
                  FiRows(
                    children: [
                      for (final m in data.months)
                        FiDataRow(
                          label: '${_mesPorExtenso(m.month)} · ${categoryLabel(m.category)}',
                          value: formatCurrency(m.irAmount),
                          note: m.observation,
                        ),
                    ],
                  ),
                ],

                const SizedBox(height: FiSpace.s6),
                Text(
                  'VENDAS',
                  style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                ),
                const SizedBox(height: FiSpace.s3),
                FiRows(
                  children: [
                    for (final t in data.trades)
                      FiDataRow(
                        label: t.ticker,
                        detail:
                            '${t.quantity} un. · venda ${formatCurrency(t.sellPrice)}',
                        value:
                            '${t.netProfit >= 0 ? '+' : ''}${formatCurrency(t.netProfit)}',
                        valueColor: fiDirectionColor(
                          t.netProfit >= 0 ? 1 : -1,
                          brightness,
                        ),
                      ),
                  ],
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}
