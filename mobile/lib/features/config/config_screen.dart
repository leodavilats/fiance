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
import '../../core/widgets/ticker_autocomplete_field.dart';

class ConfigScreen extends ConsumerWidget {
  const ConfigScreen({super.key});

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
                  // Antes do signOut: depois dele o token de autenticação
                  // já não existe para autorizar o DELETE.
                  await ref
                      .read(notificationsServiceProvider)
                      .unregisterToken();
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
                      title: const Text('Yield desejado — BDRs'),
                      trailing: Text(
                        formatPercent(prefs.desiredYieldBdr * 100),
                      ),
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.layers_outlined),
                      title: const Text('Yield desejado — ETFs'),
                      trailing: Text(
                        formatPercent(prefs.desiredYieldEtf * 100),
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
                      subtitle: const Text('Sempre imediato, é um alerta de risco'),
                      value: prefs.notifyPriceAlerts,
                      onChanged: (v) async {
                        await ref
                            .read(apiRepositoryProvider)
                            .savePreferences(
                              passiveIncomeGoal: prefs.passiveIncomeGoal,
                              notifyPriceAlerts: v,
                            );
                        ref.invalidate(preferencesProvider);
                      },
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.auto_awesome_outlined),
                      title: const Text('Resumo de oportunidades'),
                      subtitle: Text(
                        'Cadência: ${_frequencyLabel(prefs.opportunitiesFrequency)}',
                      ),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => _pickFrequency(context, ref, prefs),
                    ),
                  ],
                ),
                _SettingsCard(
                  icon: Icons.tune_outlined,
                  title: 'Preferências de recomendação',
                  children: [
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.shield_outlined),
                      title: const Text('Perfil de risco'),
                      subtitle: Text(_riskProfileLabel(prefs.riskProfile)),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => _pickRiskProfile(context, ref, prefs),
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.category_outlined),
                      title: const Text('Categorias preferidas'),
                      subtitle: Text(
                        prefs.preferredCategories.isEmpty
                            ? 'Nenhuma — todas pesam igual'
                            : prefs.preferredCategories
                                  .map(categoryLabel)
                                  .join(', '),
                      ),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => _pickPreferredCategories(context, ref, prefs),
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.factory_outlined),
                      title: const Text('Setores preferidos'),
                      subtitle: Text(
                        prefs.preferredSectors.isEmpty
                            ? 'Nenhum'
                            : prefs.preferredSectors.join(', '),
                      ),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => _editCsvList(
                        context,
                        ref,
                        prefs,
                        title: 'Setores preferidos',
                        hint: 'Ex.: Energia, Bancos, Varejo',
                        initial: prefs.preferredSectors,
                        apply: (values) => ref
                            .read(apiRepositoryProvider)
                            .savePreferences(
                              passiveIncomeGoal: prefs.passiveIncomeGoal,
                              preferredSectors: values,
                            ),
                      ),
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.block_outlined),
                      title: const Text('Ativos excluídos'),
                      subtitle: Text(
                        prefs.excludedTickers.isEmpty
                            ? 'Nenhum'
                            : prefs.excludedTickers.join(', '),
                      ),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => _editCsvList(
                        context,
                        ref,
                        prefs,
                        title: 'Ativos excluídos das oportunidades',
                        hint: 'Ex.: MGLU3, IRBR3',
                        initial: prefs.excludedTickers,
                        apply: (values) => ref
                            .read(apiRepositoryProvider)
                            .savePreferences(
                              passiveIncomeGoal: prefs.passiveIncomeGoal,
                              excludedTickers: values
                                  .map((v) => v.toUpperCase())
                                  .toList(),
                            ),
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

const _frequencyLabels = {
  'off': 'Desativado',
  'daily': 'Diária',
  'weekly': 'Semanal',
  'monthly': 'Mensal',
};

String _frequencyLabel(String value) => _frequencyLabels[value] ?? value;

const _riskProfileLabels = {
  'conservative': 'Conservador',
  'moderate': 'Moderado',
  'aggressive': 'Arrojado',
};

String _riskProfileLabel(String value) => _riskProfileLabels[value] ?? value;

const _preferenceCategories = ['acoes_br', 'bdrs', 'fiis', 'etfs', 'renda_fixa'];

Future<void> _pickFrequency(
  BuildContext context,
  WidgetRef ref,
  Preferences prefs,
) async {
  final picked = await showDialog<String>(
    context: context,
    builder: (context) => SimpleDialog(
      title: const Text('Cadência do resumo de oportunidades'),
      children: [
        RadioGroup<String>(
          groupValue: prefs.opportunitiesFrequency,
          onChanged: (v) => Navigator.pop(context, v),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: _frequencyLabels.entries
                .map((e) => RadioListTile<String>(value: e.key, title: Text(e.value)))
                .toList(),
          ),
        ),
      ],
    ),
  );
  if (picked == null || picked == prefs.opportunitiesFrequency) return;

  await ref
      .read(apiRepositoryProvider)
      .savePreferences(
        passiveIncomeGoal: prefs.passiveIncomeGoal,
        opportunitiesFrequency: picked,
      );
  ref.invalidate(preferencesProvider);
}

Future<void> _pickRiskProfile(
  BuildContext context,
  WidgetRef ref,
  Preferences prefs,
) async {
  final picked = await showDialog<String>(
    context: context,
    builder: (context) => SimpleDialog(
      title: const Text('Perfil de risco'),
      children: [
        RadioGroup<String>(
          groupValue: prefs.riskProfile,
          onChanged: (v) => Navigator.pop(context, v),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: _riskProfileLabels.entries
                .map((e) => RadioListTile<String>(value: e.key, title: Text(e.value)))
                .toList(),
          ),
        ),
      ],
    ),
  );
  if (picked == null || picked == prefs.riskProfile) return;

  await ref
      .read(apiRepositoryProvider)
      .savePreferences(
        passiveIncomeGoal: prefs.passiveIncomeGoal,
        riskProfile: picked,
      );
  ref.invalidate(preferencesProvider);
}

Future<void> _pickPreferredCategories(
  BuildContext context,
  WidgetRef ref,
  Preferences prefs,
) async {
  var selected = {...prefs.preferredCategories};

  final confirmed = await showDialog<bool>(
    context: context,
    builder: (context) => StatefulBuilder(
      builder: (context, setState) => AlertDialog(
        title: const Text('Categorias preferidas'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: _preferenceCategories
              .map(
                (c) => CheckboxListTile(
                  value: selected.contains(c),
                  title: Text(categoryLabel(c)),
                  onChanged: (v) => setState(() {
                    if (v == true) {
                      selected.add(c);
                    } else {
                      selected.remove(c);
                    }
                  }),
                ),
              )
              .toList(),
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
    ),
  );
  if (confirmed != true) return;

  await ref
      .read(apiRepositoryProvider)
      .savePreferences(
        passiveIncomeGoal: prefs.passiveIncomeGoal,
        preferredCategories: selected.toList(),
      );
  ref.invalidate(preferencesProvider);
}

Future<void> _editCsvList(
  BuildContext context,
  WidgetRef ref,
  Preferences prefs, {
  required String title,
  required String hint,
  required List<String> initial,
  required Future<void> Function(List<String> values) apply,
}) async {
  final controller = TextEditingController(text: initial.join(', '));

  final confirmed = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(title),
      content: TextField(
        controller: controller,
        decoration: InputDecoration(hintText: hint),
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

  final values = controller.text
      .split(',')
      .map((v) => v.trim())
      .where((v) => v.isNotEmpty)
      .toList();
  await apply(values);
  ref.invalidate(preferencesProvider);
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
              TickerAutocompleteField(controller: tickerCtrl),
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
