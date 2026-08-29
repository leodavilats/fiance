import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/format.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';

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
        final totalColor = data.totalRealizedPnl >= 0
            ? fiDirectionColor(1, brightness)
            : fiDirectionColor(-1, brightness);

        return Card(
          margin: EdgeInsets.zero,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ListTile(
                title: const Text(
                  'Operações encerradas',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                subtitle: RichText(
                  text: TextSpan(
                    style: DefaultTextStyle.of(context).style.copyWith(
                      color: fiInk2(context),
                      fontSize: 12,
                    ),
                    children: [
                      const TextSpan(text: 'Lucro/prejuízo realizado: '),
                      TextSpan(
                        text: formatCurrency(data.totalRealizedPnl),
                        style: TextStyle(
                          color: totalColor,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      TextSpan(text: ' · IR: ${formatCurrency(data.totalIrPaid)}'),
                    ],
                  ),
                ),
                trailing: Icon(
                  _expanded ? Icons.expand_less : Icons.expand_more,
                ),
                onTap: () => setState(() => _expanded = !_expanded),
              ),
              if (_expanded)
                ...data.trades.map(
                  (t) => Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 6,
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                t.ticker,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              Text(
                                '${t.quantity} un. · venda ${formatCurrency(t.sellPrice)}',
                                style: TextStyle(
                                  color: fiInk2(context),
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Text(
                          '${t.netProfit >= 0 ? '+' : ''}${formatCurrency(t.netProfit)}',
                          style: TextStyle(
                            color: t.netProfit >= 0
                                ? fiDirectionColor(1, brightness)
                                : fiDirectionColor(-1, brightness),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 8),
            ],
          ),
        );
      },
    );
  }
}
