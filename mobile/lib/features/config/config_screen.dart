import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/sector_translations.dart';
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

  Future<void> _sendTestNotification(BuildContext context, WidgetRef ref) async {
    final notifications = ref.read(notificationsServiceProvider);
    final messenger = ScaffoldMessenger.of(context);

    if (notifications.permissionStatus == AuthorizationStatus.denied) {
      messenger.showSnackBar(
        const SnackBar(
          content: Text(
            'Permissão de notificação negada — habilite nas configurações do Android.',
          ),
        ),
      );
      return;
    }

    try {
      final result = await ref.read(apiRepositoryProvider).sendTestNotification();
      final tokensFound = result['tokens_found'] as int? ?? 0;
      final firebaseConfigured = result['firebase_configured'] as bool? ?? false;

      String message;
      if (tokensFound == 0) {
        message =
            'Nenhum dispositivo registrado — o token de notificação não chegou a ser salvo no servidor.';
      } else if (!firebaseConfigured) {
        message =
            'O servidor NÃO tem a credencial do Firebase configurada — a notificação foi só simulada, nunca vai chegar. Configure FIREBASE_SERVICE_ACCOUNT_JSON no ambiente do backend.';
      } else {
        message =
            'Enviado de verdade para $tokensFound dispositivo(s) — deve chegar em poucos segundos.';
      }

      messenger.showSnackBar(
        SnackBar(content: Text(message), duration: const Duration(seconds: 6)),
      );
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('Erro ao enviar: $e')));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final preferences = ref.watch(preferencesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Configurações')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(12, 12, 12, 24),
        children: [
          _SettingsCard(
            icon: Icons.person_outline,
            title: 'Conta',
            children: [
              if (user != null)
                ListTile(
                  contentPadding: EdgeInsets.zero,
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
              ListTile(
                contentPadding: EdgeInsets.zero,
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
          _SettingsCard(
            icon: Icons.palette_outlined,
            title: 'Aparência',
            children: [
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                secondary: Icon(
                  ref.watch(themeModeProvider) == ThemeMode.dark
                      ? Icons.dark_mode_outlined
                      : Icons.light_mode_outlined,
                ),
                title: const Text('Tema escuro'),
                value: ref.watch(themeModeProvider) == ThemeMode.dark,
                onChanged: (_) => ref.read(themeModeProvider.notifier).toggle(),
              ),
            ],
          ),
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
                _SettingsCard(
                  icon: Icons.account_balance_wallet_outlined,
                  title: 'Preferências financeiras',
                  children: [
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(
                        Icons.account_balance_wallet_outlined,
                      ),
                      title: const Text('Caixa disponível'),
                      subtitle: Text(formatCurrency(prefs.cashAvailable)),
                      trailing: const Icon(Icons.edit, size: 18),
                      onTap: () =>
                          _editCash(context, ref, prefs.cashAvailable),
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.savings_outlined),
                      title: const Text('Yield desejado — Ações'),
                      trailing: Text(
                        formatPercent(prefs.desiredYieldStock * 100),
                      ),
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.apartment_outlined),
                      title: const Text('Yield desejado — FIIs'),
                      trailing: Text(
                        formatPercent(prefs.desiredYieldFii * 100),
                      ),
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.public_outlined),
                      title: const Text('Yield desejado — Internacional'),
                      trailing: Text(
                        formatPercent(prefs.desiredYieldInt * 100),
                      ),
                    ),
                    if (prefs.passiveIncomeGoal != null)
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.flag_outlined),
                        title: const Text('Meta de renda passiva'),
                        trailing: Text(
                          '${formatCurrency(prefs.passiveIncomeGoal)}/mês',
                        ),
                      ),
                  ],
                ),
                _SettingsCard(
                  icon: Icons.notifications_active_outlined,
                  title: 'Notificações',
                  children: [
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      secondary: const Icon(
                        Icons.notifications_active_outlined,
                      ),
                      title: const Text('Notificar alertas de preço'),
                      value: prefs.notifyPriceAlerts,
                      onChanged: (v) async {
                        await ref
                            .read(apiRepositoryProvider)
                            .savePreferences(
                              cashAvailable: prefs.cashAvailable,
                              passiveIncomeGoal: prefs.passiveIncomeGoal,
                              notifyPriceAlerts: v,
                              notifyNewOpportunities:
                                  prefs.notifyNewOpportunities,
                            );
                        ref.invalidate(preferencesProvider);
                      },
                    ),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      secondary: const Icon(Icons.auto_awesome_outlined),
                      title: const Text('Notificar novas oportunidades'),
                      value: prefs.notifyNewOpportunities,
                      onChanged: (v) async {
                        await ref
                            .read(apiRepositoryProvider)
                            .savePreferences(
                              cashAvailable: prefs.cashAvailable,
                              passiveIncomeGoal: prefs.passiveIncomeGoal,
                              notifyPriceAlerts: prefs.notifyPriceAlerts,
                              notifyNewOpportunities: v,
                            );
                        ref.invalidate(preferencesProvider);
                      },
                    ),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: OutlinedButton.icon(
                        onPressed: () => _sendTestNotification(context, ref),
                        icon: const Icon(Icons.send_outlined, size: 18),
                        label: const Text('Enviar notificação de teste'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          _SettingsCard(
            icon: Icons.pie_chart_outline,
            title: 'Metas de alocação por categoria',
            children: const [_GoalsSection()],
          ),
          _SettingsCard(
            icon: Icons.donut_small_outlined,
            title: 'Metas de alocação por setor',
            children: const [_SectorGoalsSection()],
          ),
          _SettingsCard(
            icon: Icons.notifications_none,
            title: 'Alertas de preço',
            children: const [_AlertsSection()],
          ),
        ],
      ),
    );
  }
}

class _SettingsCard extends StatelessWidget {
  const _SettingsCard({
    required this.icon,
    required this.title,
    required this.children,
  });

  final IconData icon;
  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, size: 18, color: Colors.grey.shade600),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ...children,
          ],
        ),
      ),
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
                    Expanded(child: Text(translateSector(g.sector))),
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
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                initialValue: condition,
                decoration: const InputDecoration(labelText: 'Condição'),
                items: const [
                  DropdownMenuItem(value: 'below', child: Text('Abaixo de')),
                  DropdownMenuItem(value: 'above', child: Text('Acima de')),
                ],
                onChanged: (v) => setState(() => condition = v!),
              ),
              const SizedBox(height: 16),
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
