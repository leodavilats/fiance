import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';

void showAssetDetailSheet(BuildContext context, String ticker) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    builder: (context) => DraggableScrollableSheet(
      initialChildSize: 0.7,
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

    return analysisFuture.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, _) => Center(child: Text('Erro ao analisar $ticker: $err')),
      data: (a) => ListView(
        controller: scrollController,
        padding: const EdgeInsets.all(20),
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    a.symbol,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  if (a.name != null)
                    Text(
                      a.name!,
                      style: TextStyle(color: Colors.grey.shade600),
                    ),
                ],
              ),
              _VerdictPill(verdict: a.verdict, label: a.label),
            ],
          ),
          const SizedBox(height: 16),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            childAspectRatio: 2.6,
            children: [
              _StatCard(label: 'Preço atual', value: formatCurrency(a.price)),
              _StatCard(
                label: 'Preço justo (consenso)',
                value: formatCurrency(a.consensus),
              ),
              _StatCard(
                label: 'Margem de segurança',
                value: formatPercent(a.marginOfSafety),
              ),
              _StatCard(label: 'Setor', value: a.sector ?? '—'),
            ],
          ),
          const SizedBox(height: 16),
          const Text(
            'Preço justo detalhado',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          if (a.bazin != null)
            _KeyValueRow(label: 'Bazin', value: formatCurrency(a.bazin)),
          if (a.graham != null)
            _KeyValueRow(label: 'Graham', value: formatCurrency(a.graham)),
          const SizedBox(height: 16),
          const Text(
            'Indicadores técnicos',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          _KeyValueRow(label: 'Tendência', value: a.trend),
          _KeyValueRow(
            label: 'RSI (14)',
            value: a.rsi14?.toStringAsFixed(1) ?? '—',
          ),
          if (a.reasons.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text(
              'Por que essa decisão?',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ...a.reasons.map(
              (r) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Text('• $r'),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

final _assetAnalysisProvider = FutureProvider.autoDispose
    .family<AssetAnalysis, String>((ref, ticker) {
      return ref.watch(apiRepositoryProvider).analyzeAsset(ticker);
    });

class _VerdictPill extends StatelessWidget {
  const _VerdictPill({required this.verdict, required this.label});

  final String verdict;
  final String label;

  Color _color() {
    if (verdict.contains('BUY')) return Colors.green.shade700;
    if (verdict.contains('SELL')) return Colors.red.shade700;
    return Colors.grey.shade700;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: _color().withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        label,
        style: TextStyle(color: _color(), fontWeight: FontWeight.bold),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            label,
            style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
          ),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}

class _KeyValueRow extends StatelessWidget {
  const _KeyValueRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
