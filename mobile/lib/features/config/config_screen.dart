import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/theme_provider.dart';

class ConfigScreen extends ConsumerWidget {
  const ConfigScreen({super.key});

  Future<void> _editCash(
    BuildContext context,
    WidgetRef ref,
    double current,
  ) async {
    final ctrl = TextEditingController(text: current.toStringAsFixed(2));

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Caixa disponível'),
        content: TextField(
          controller: ctrl,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(prefixText: 'R\$ '),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Salvar'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;
    final value = double.tryParse(ctrl.text.replaceAll(',', '.'));
    if (value == null) return;

    await ref.read(apiRepositoryProvider).savePreferences(cashAvailable: value);
    ref.invalidate(preferencesProvider);
    ref.invalidate(dashboardProvider);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final preferences = ref.watch(preferencesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Configurações')),
      body: ListView(
        children: [
          if (user != null)
            ListTile(
              leading: CircleAvatar(
                backgroundImage: user.picture.isNotEmpty
                    ? NetworkImage(user.picture)
                    : null,
                child: user.picture.isEmpty
                    ? Text(user.name.isNotEmpty ? user.name[0] : '?')
                    : null,
              ),
              title: Text(user.name),
              subtitle: Text(user.email),
            ),
          const Divider(),
          SwitchListTile(
            secondary: Icon(
              ref.watch(themeModeProvider) == ThemeMode.dark
                  ? Icons.dark_mode_outlined
                  : Icons.light_mode_outlined,
            ),
            title: const Text('Tema escuro'),
            value: ref.watch(themeModeProvider) == ThemeMode.dark,
            onChanged: (_) => ref.read(themeModeProvider.notifier).toggle(),
          ),
          const Divider(),
          preferences.when(
            loading: () => const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (err, _) => Padding(
              padding: const EdgeInsets.all(16),
              child: Text('Erro ao carregar preferências: $err'),
            ),
            data: (prefs) => Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.account_balance_wallet_outlined),
                  title: const Text('Caixa disponível'),
                  subtitle: Text(formatCurrency(prefs.cashAvailable)),
                  trailing: const Icon(Icons.edit, size: 18),
                  onTap: () => _editCash(context, ref, prefs.cashAvailable),
                ),
                ListTile(
                  leading: const Icon(Icons.savings_outlined),
                  title: const Text('Yield desejado — Ações'),
                  trailing: Text(formatPercent(prefs.desiredYieldStock * 100)),
                ),
                ListTile(
                  leading: const Icon(Icons.apartment_outlined),
                  title: const Text('Yield desejado — FIIs'),
                  trailing: Text(formatPercent(prefs.desiredYieldFii * 100)),
                ),
                ListTile(
                  leading: const Icon(Icons.public_outlined),
                  title: const Text('Yield desejado — Internacional'),
                  trailing: Text(formatPercent(prefs.desiredYieldInt * 100)),
                ),
                if (prefs.passiveIncomeGoal != null)
                  ListTile(
                    leading: const Icon(Icons.flag_outlined),
                    title: const Text('Meta de renda passiva'),
                    trailing: Text(
                      '${formatCurrency(prefs.passiveIncomeGoal)}/mês',
                    ),
                  ),
              ],
            ),
          ),
          const Divider(),
          const _SectionHeader('Metas de alocação por categoria'),
          const _GoalsSection(),
          const Divider(),
          const _SectionHeader('Metas de alocação por setor'),
          const _SectorGoalsSection(),
          const Divider(),
          const _SectionHeader('Alertas de preço'),
          const _AlertsSection(),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Sair'),
            onTap: () async {
              await ref.read(authServiceProvider).signOut();
              ref.read(currentUserProvider.notifier).state = null;
              if (context.mounted) context.go('/login');
            },
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.title);

  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
      child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
    );
  }
}

class _GoalsSection extends ConsumerStatefulWidget {
  const _GoalsSection();

  @override
  ConsumerState<_GoalsSection> createState() => _GoalsSectionState();
}

class _GoalsSectionState extends ConsumerState<_GoalsSection> {
  List<Goal>? _editing;

  @override
  Widget build(BuildContext context) {
    final goals = ref.watch(goalsProvider);

    return goals.when(
      loading: () => const Padding(
        padding: EdgeInsets.all(16),
        child: LinearProgressIndicator(),
      ),
      error: (err, _) =>
          Padding(padding: const EdgeInsets.all(16), child: Text('Erro: $err')),
      data: (data) {
        final items = _editing ?? data;
        final total = items.fold<double>(0, (sum, g) => sum + g.targetPct);

        return Column(
          children: [
            ...items.map(
              (g) => Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 4,
                ),
                child: Row(
                  children: [
                    Expanded(child: Text(categoryLabel(g.category))),
                    SizedBox(
                      width: 160,
                      child: Slider(
                        value: g.targetPct.clamp(0, 100),
                        max: 100,
                        divisions: 100,
                        label: '${g.targetPct.toStringAsFixed(0)}%',
                        onChanged: (v) => setState(() {
                          _editing = items
                              .map(
                                (it) => it.category == g.category
                                    ? it.copyWith(targetPct: v)
                                    : it,
                              )
                              .toList();
                        }),
                      ),
                    ),
                    SizedBox(
                      width: 44,
                      child: Text('${g.targetPct.toStringAsFixed(0)}%'),
                    ),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Total: ${total.toStringAsFixed(0)}%',
                    style: TextStyle(
                      color: (total - 100).abs() < 0.5
                          ? gainColor(Theme.of(context).brightness)
                          : lossColor(Theme.of(context).brightness),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  FilledButton(
                    onPressed: _editing == null || (total - 100).abs() >= 0.5
                        ? null
                        : () async {
                            await ref
                                .read(apiRepositoryProvider)
                                .saveGoals(_editing!);
                            ref.invalidate(goalsProvider);
                            setState(() => _editing = null);
                          },
                    child: const Text('Salvar'),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}

const _sectorFallbackList = [
  'Financeiro',
  'Energia',
  'Varejo',
  'Tecnologia',
  'Saúde',
  'Outros',
];

class _SectorGoalsSection extends ConsumerStatefulWidget {
  const _SectorGoalsSection();

  @override
  ConsumerState<_SectorGoalsSection> createState() =>
      _SectorGoalsSectionState();
}

class _SectorGoalsSectionState extends ConsumerState<_SectorGoalsSection> {
  List<SectorGoal>? _editing;

  @override
  Widget build(BuildContext context) {
    final goals = ref.watch(sectorGoalsProvider);

    return goals.when(
      loading: () => const Padding(
        padding: EdgeInsets.all(16),
        child: LinearProgressIndicator(),
      ),
      error: (err, _) =>
          Padding(padding: const EdgeInsets.all(16), child: Text('Erro: $err')),
      data: (data) {
        final items = data.isNotEmpty
            ? data
            : _sectorFallbackList
                  .map(
                    (s) => SectorGoal(
                      sector: s,
                      targetPct: 100 / _sectorFallbackList.length,
                    ),
                  )
                  .toList();
        final current = _editing ?? items;
        final total = current.fold<double>(0, (sum, g) => sum + g.targetPct);

        return Column(
          children: [
            ...current.map(
              (g) => Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 4,
                ),
                child: Row(
                  children: [
                    Expanded(child: Text(g.sector)),
                    SizedBox(
                      width: 160,
                      child: Slider(
                        value: g.targetPct.clamp(0, 100),
                        max: 100,
                        divisions: 100,
                        label: '${g.targetPct.toStringAsFixed(0)}%',
                        onChanged: (v) => setState(() {
                          _editing = current
                              .map(
                                (it) => it.sector == g.sector
                                    ? it.copyWith(targetPct: v)
                                    : it,
                              )
                              .toList();
                        }),
                      ),
                    ),
                    SizedBox(
                      width: 44,
                      child: Text('${g.targetPct.toStringAsFixed(0)}%'),
                    ),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Total: ${total.toStringAsFixed(0)}%'),
                  FilledButton(
                    onPressed: _editing == null
                        ? null
                        : () async {
                            await ref
                                .read(apiRepositoryProvider)
                                .saveSectorGoals(_editing!);
                            ref.invalidate(sectorGoalsProvider);
                            setState(() => _editing = null);
                          },
                    child: const Text('Salvar'),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}

class _AlertsSection extends ConsumerWidget {
  const _AlertsSection();

  Future<void> _createAlert(BuildContext context, WidgetRef ref) async {
    final tickerCtrl = TextEditingController();
    final priceCtrl = TextEditingController();
    String condition = 'below';

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Novo alerta de preço'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: tickerCtrl,
                textCapitalization: TextCapitalization.characters,
                decoration: const InputDecoration(labelText: 'Ticker'),
              ),
              DropdownButtonFormField<String>(
                initialValue: condition,
                decoration: const InputDecoration(labelText: 'Condição'),
                items: const [
                  DropdownMenuItem(value: 'below', child: Text('Abaixo de')),
                  DropdownMenuItem(value: 'above', child: Text('Acima de')),
                ],
                onChanged: (v) => setState(() => condition = v!),
              ),
              TextField(
                controller: priceCtrl,
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                decoration: const InputDecoration(
                  labelText: 'Preço alvo (R\$)',
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Criar'),
            ),
          ],
        ),
      ),
    );

    if (confirmed != true) return;
    final ticker = tickerCtrl.text.trim().toUpperCase();
    final price = double.tryParse(priceCtrl.text.replaceAll(',', '.'));
    if (ticker.isEmpty || price == null) return;

    await ref
        .read(apiRepositoryProvider)
        .createAlert(ticker: ticker, condition: condition, targetPrice: price);
    ref.invalidate(alertsProvider);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final alerts = ref.watch(alertsProvider);

    return Column(
      children: [
        alerts.when(
          loading: () => const Padding(
            padding: EdgeInsets.all(16),
            child: LinearProgressIndicator(),
          ),
          error: (err, _) => Padding(
            padding: const EdgeInsets.all(16),
            child: Text('Erro: $err'),
          ),
          data: (items) {
            if (items.isEmpty) {
              return const Padding(
                padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Text(
                  'Nenhum alerta configurado',
                  style: TextStyle(color: Colors.grey),
                ),
              );
            }
            return Column(
              children: items
                  .map(
                    (a) => ListTile(
                      title: Text(a.ticker),
                      subtitle: Text(
                        '${a.condition == 'below' ? 'Abaixo de' : 'Acima de'} ${formatCurrency(a.targetPrice)}'
                        '${a.triggeredAt != null ? ' · disparado' : ''}',
                      ),
                      trailing: IconButton(
                        icon: const Icon(Icons.delete_outline),
                        onPressed: () async {
                          await ref
                              .read(apiRepositoryProvider)
                              .deleteAlert(a.id);
                          ref.invalidate(alertsProvider);
                        },
                      ),
                    ),
                  )
                  .toList(),
            );
          },
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton.icon(
              onPressed: () => _createAlert(context, ref),
              icon: const Icon(Icons.add_alert_outlined),
              label: const Text('Novo alerta'),
            ),
          ),
        ),
      ],
    );
  }
}
