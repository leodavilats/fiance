import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';

class SectorsTab extends ConsumerWidget {
  const SectorsTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final category = ref.watch(sectorsCategoryProvider);
    final sectors = ref.watch(sectorsSummaryProvider);

    const categories = {
      'acoes_br': 'Ações BR',
      'fiis': 'FIIs',
      'acoes_int': 'Ações INT',
      'cripto': 'Cripto',
    };

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: categories.entries
                  .map((e) => Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: ChoiceChip(
                          label: Text(e.value),
                          selected: category == e.key,
                          onSelected: (_) => ref.read(sectorsCategoryProvider.notifier).state = e.key,
                        ),
                      ))
                  .toList(),
            ),
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: () async => ref.invalidate(sectorsSummaryProvider),
            child: sectors.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, _) => Center(child: Text('Erro: $err')),
              data: (items) {
                if (items.isEmpty) {
                  return ListView(
                    children: const [
                      Padding(
                        padding: EdgeInsets.all(32),
                        child: Text('Nenhum setor encontrado', textAlign: TextAlign.center),
                      ),
                    ],
                  );
                }
                return ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: items.length,
                  itemBuilder: (context, index) => _SectorCard(sector: items[index]),
                );
              },
            ),
          ),
        ),
      ],
    );
  }
}

class _SectorCard extends StatelessWidget {
  const _SectorCard({required this.sector});

  final SectorSummary sector;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(sector.sector, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                Text('${sector.count} ativos', style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                Text('Score médio: ${sector.avgScore.toStringAsFixed(1)}',
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                const SizedBox(width: 12),
                Text('DY médio: ${formatPercent(sector.avgDy)}',
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
              ],
            ),
            if (sector.topAssets.isNotEmpty) ...[
              const Divider(height: 16),
              Wrap(
                spacing: 8,
                runSpacing: 4,
                children: sector.topAssets
                    .map((a) => Chip(
                          label: Text('${a.ticker} · DY ${formatPercent(a.dividendYield)}',
                              style: const TextStyle(fontSize: 11)),
                          padding: EdgeInsets.zero,
                          visualDensity: VisualDensity.compact,
                        ))
                    .toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
