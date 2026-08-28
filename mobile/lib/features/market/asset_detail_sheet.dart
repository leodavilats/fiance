import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/sector_translations.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';

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
      error: (err, _) => FiErrorState(error: err, action: 'analisar $ticker'),
      data: (a) => ListView(
        controller: scrollController,
        padding: const EdgeInsets.all(20),
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
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
                        style: TextStyle(color: fiInk2(context)),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              _VerdictPill(verdict: a.verdict, label: a.label),
            ],
          ),
          const SizedBox(height: 16),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            childAspectRatio: 2.6,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
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
              _StatCard(label: 'Setor', value: translateSector(a.sector)),
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
          if (a.falsifiers.isNotEmpty) ...[
            const SizedBox(height: 16),
            // Um veredito sem condição de queda é fé: explica como se chegou
            // ali, mas não diz o que precisaria acontecer para deixar de valer.
            const Text(
              'O que faria a tese mudar',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ...a.falsifiers.map(
              (f) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Text('• ${f.condition} → ${f.becomesLabel}'),
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

  Color _color(Brightness brightness) {
    if (verdict.contains('BUY')) {
      return fiStateColor(FiState.favorable, brightness);
    }
    if (verdict.contains('SELL')) {
      return fiStateColor(FiState.adverse, brightness);
    }
    return fiStateColor(FiState.indeterminate, brightness);
  }

  @override
  Widget build(BuildContext context) {
    final color = _color(Theme.of(context).brightness);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        label,
        style: TextStyle(color: color, fontWeight: FontWeight.bold),
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
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkPanel2 : AppColors.lightPanel2,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: isDark ? AppColors.darkMuted : AppColors.lightMuted,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: scheme.onSurface,
            ),
          ),
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
