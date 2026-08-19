import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import 'asset_detail_sheet.dart';

const _actionLabels = {
  'comprar_mais': 'Comprar mais',
  'vender': 'Vender',
  'realocar': 'Realocar',
  'manter': 'Não fazer nada',
};

class RebalanceTab extends ConsumerWidget {
  const RebalanceTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final result = ref.watch(rebalanceSuggestionsProvider);
    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(rebalanceSuggestionsProvider),
      child: result.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => ListView(
          children: [
            const SizedBox(height: 80),
            Center(child: Text('Erro ao carregar sugestões: $err')),
          ],
        ),
        data: (suggestions) {
          if (suggestions.items.isEmpty) {
            return ListView(
              children: const [
                Padding(
                  padding: EdgeInsets.all(32),
                  child: Text(
                    'Nenhum ativo na carteira para avaliar. Cadastre posições em Meus Ativos.',
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            );
          }
          return ListView(
            padding: const EdgeInsets.all(12),
            children: [
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 4, vertical: 4),
                child: Text(
                  'Para cada ativo já na sua carteira: comprar mais, vender, realocar ou '
                  'não fazer nada — considerando seu perfil de risco, preferências e '
                  'ativos excluídos configurados em Config.',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ),
              if (suggestions.taxDisclaimer != null)
                Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.orange.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.orange.withValues(alpha: 0.4)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 18),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          suggestions.taxDisclaimer!,
                          style: const TextStyle(fontSize: 11.5, color: Colors.orange),
                        ),
                      ),
                    ],
                  ),
                ),
              ...suggestions.items.map(
                (item) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _RebalanceCard(item: item),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _RebalanceCard extends StatelessWidget {
  const _RebalanceCard({required this.item});

  final RebalanceItem item;

  Color _verdictColor(Brightness brightness) {
    switch (item.verdict) {
      case 'STRONG_BUY':
      case 'BUY':
        return gainColor(brightness);
      case 'STRONG_SELL':
      case 'SELL':
        return lossColor(brightness);
      default:
        return Colors.grey.shade700;
    }
  }

  Color _actionColor(Brightness brightness) {
    switch (item.action) {
      case 'comprar_mais':
        return gainColor(brightness);
      case 'vender':
        return lossColor(brightness);
      case 'realocar':
        return Colors.orange;
      default:
        return Colors.grey.shade600;
    }
  }

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final verdictColor = _verdictColor(brightness);
    final actionColor = _actionColor(brightness);

    return Card(
      margin: EdgeInsets.zero,
      elevation: 1.5,
      child: InkWell(
        onTap: () => showAssetDetailSheet(context, item.ticker),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              item.ticker,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: verdictColor.withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                item.verdict,
                                style: TextStyle(
                                  color: verdictColor,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 11,
                                ),
                              ),
                            ),
                          ],
                        ),
                        Text(
                          item.name ?? categoryLabel(item.category),
                          style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: actionColor.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          _actionLabels[item.action] ?? item.action,
                          style: TextStyle(
                            color: actionColor,
                            fontWeight: FontWeight.w700,
                            fontSize: 12,
                          ),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        formatCurrency(item.currentValue),
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                      ),
                      if (item.pnlPct != null)
                        Text(
                          '${item.pnlPct! >= 0 ? '+' : ''}${item.pnlPct!.toStringAsFixed(1)}%',
                          style: TextStyle(
                            fontSize: 11,
                            color: item.pnlPct! >= 0 ? gainColor(brightness) : lossColor(brightness),
                          ),
                        ),
                    ],
                  ),
                ],
              ),
              if (item.realocarPara != null) ...[
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.grey.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.arrow_forward, size: 14),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          'Realocar para ${item.realocarPara!.ticker} '
                          '(${categoryLabel(item.realocarPara!.category)}, '
                          'score ${item.realocarPara!.score.toStringAsFixed(0)})',
                          style: const TextStyle(fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              if (item.reasons.isNotEmpty) ...[
                const SizedBox(height: 8),
                ...item.reasons.map(
                  (reason) => Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text(
                      '• $reason',
                      style: TextStyle(fontSize: 11.5, color: Colors.grey.shade700),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
