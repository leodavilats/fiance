import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/format.dart';
import '../../../core/labels.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';

class FiClosedTradesSection extends ConsumerStatefulWidget {
  const FiClosedTradesSection({super.key});

  @override
  ConsumerState<FiClosedTradesSection> createState() =>
      _FiClosedTradesSectionState();
}

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
                      TextSpan(
                        text: ' · IR apurado: ${formatCurrency(data.totalIrPaid)}',
                      ),
                    ],
                  ),
                ),
                trailing: Icon(
                  _expanded ? Icons.expand_less : Icons.expand_more,
                ),
                onTap: () => setState(() => _expanded = !_expanded),
              ),
              if (_expanded && data.months.isNotEmpty) ...[
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Apuração por mês',
                        style: FiType.label,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'O imposto é do mês, não da venda: lucros e prejuízos do '
                        'mesmo mês e da mesma categoria se compensam.',
                        style: FiType.caption.copyWith(color: fiInk2(context)),
                      ),
                    ],
                  ),
                ),
                ...data.months.map(
                  (m) => Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 6,
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                '${_mesPorExtenso(m.month)} · '
                                '${categoryLabel(m.category)}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                            Text(
                              formatCurrency(m.irAmount),
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text(
                          m.observation,
                          style: FiType.caption.copyWith(
                            color: fiInk2(context),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const Divider(height: 16),
              ],
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
                                style: FiType.caption.copyWith(color: fiInk2(context)),
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
