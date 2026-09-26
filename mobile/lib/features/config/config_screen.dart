import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/nav_action.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/legal_links.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/theme_provider.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';
import '../../core/widgets/error_state.dart';
import 'delete_account_screen.dart';
import '../../core/widgets/controls.dart';

class ConfigScreen extends ConsumerWidget {
  const ConfigScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final preferences = ref.watch(preferencesProvider);
    final alertas = ref.watch(alertsProvider);
    final escuro = ref.watch(themeModeProvider) == ThemeMode.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Você'),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          FiLayout.scrollTail,
        ),
        children: [
          const FiIdentity(),
          const SizedBox(height: FiSpace.s5),
          FiRows(
            children: [
              FiDataRow(
                label: 'Como eu invisto',
                detail: preferences.maybeWhen(
                  data: _investingSummary,
                  orElse: () => 'Perfil, categorias, setores e metas',
                ),
                onTap: () => context.go('/voce/investir'),
              ),
              FiDataRow(
                label: 'O que chega até você',
                detail: preferences.maybeWhen(
                  data: (p) => _notificationsSummary(p, alertas.valueOrNull?.length),
                  orElse: () => 'Notificações e alertas de preço',
                ),
                onTap: () => context.go('/voce/avisos'),
              ),
              FiDataRow(
                label: 'Aparência',
                detail: escuro ? 'Tema escuro' : 'Tema claro',
                onTap: () => context.go('/voce/aparencia'),
              ),
              FiDataRow(
                label: 'Conta',
                detail: 'Indicação, termos, seus dados e exclusão',
                onTap: () => context.go('/voce/conta'),
              ),
            ],
          ),
          preferences.maybeWhen(
            error: (err, _) => Padding(
              padding: const EdgeInsets.only(top: FiSpace.s6),
              child: FiErrorState(
                error: err,
                action: 'carregar suas preferências',
                onRetry: () => ref.invalidate(preferencesProvider),
              ),
            ),
            orElse: () => const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}

String _investingSummary(Preferences p) {
  final partes = <String>[
    'perfil ${_riskProfileLabel(p.riskProfile).toLowerCase()}',
    if (p.preferredCategories.isNotEmpty)
      '${p.preferredCategories.length} '
          '${p.preferredCategories.length == 1 ? 'categoria' : 'categorias'}',
    if (p.excludedTickers.isNotEmpty)
      '${p.excludedTickers.length} '
          '${p.excludedTickers.length == 1 ? 'ativo excluído' : 'ativos excluídos'}',
    if (p.passiveIncomeGoal != null)
      'meta de ${formatCurrency(p.passiveIncomeGoal)} por mês',
  ];
  return partes.join(' · ');
}

String _notificationsSummary(Preferences p, int? alertas) {
  final partes = <String>[
    'resumo ${_frequencyLabel(p.opportunitiesFrequency).toLowerCase()}',
    if (alertas != null && alertas > 0)
      '$alertas ${alertas == 1 ? 'alerta de preço' : 'alertas de preço'}'
    else if (alertas != null)
      'nenhum alerta de preço',
  ];
  return partes.join(' · ');
}

class _Axis extends StatelessWidget {
  const _Axis({required this.title, required this.children});

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          FiLayout.scrollTail,
        ),
        children: children,
      ),
    );
  }
}

class InvestingScreen extends ConsumerWidget {
  const InvestingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final preferences = ref.watch(preferencesProvider);

    return _Axis(
      title: 'Como eu invisto',
      children: [
        preferences.when(
          loading: () => const FiSkeleton(
            shape: FiSkeletonShape.row,
            count: 6,
          ),
          error: (err, _) => FiErrorState(
            error: err,
            action: 'carregar suas preferências',
            onRetry: () => ref.invalidate(preferencesProvider),
          ),
          data: (prefs) => Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              FiRecommendation(prefs: prefs),
              FiGoals(prefs: prefs),
            ],
          ),
        ),
      ],
    );
  }
}

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final preferences = ref.watch(preferencesProvider);

    return _Axis(
      title: 'O que chega até você',
      children: [
        preferences.when(
          loading: () => const FiSkeleton(
            shape: FiSkeletonShape.row,
            count: 3,
          ),
          error: (err, _) => FiErrorState(
            error: err,
            action: 'carregar suas preferências',
            onRetry: () => ref.invalidate(preferencesProvider),
          ),
          data: (prefs) => FiNotifications(prefs: prefs),
        ),
        const FiPriceAlerts(),
      ],
    );
  }
}

class AppearanceScreen extends StatelessWidget {
  const AppearanceScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const _Axis(title: 'Aparência', children: [FiAppearance()]);
  }
}

class AccountScreen extends StatelessWidget {
  const AccountScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const _Axis(
      title: 'Conta',
      children: [FiReferral(), FiLegal(), FiAccount()],
    );
  }
}

class FiIdentity extends ConsumerWidget {
  const FiIdentity({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    if (user == null) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.only(top: FiSpace.s2, bottom: FiSpace.s2),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(user.name, style: FiType.metric.copyWith(color: fiInk1(context))),
          const SizedBox(height: 2),
          Text(user.email, style: FiType.body.copyWith(color: fiInk2(context))),
        ],
      ),
    );
  }
}

class FiRecommendation extends ConsumerWidget {
  const FiRecommendation({super.key, required this.prefs});

  final Preferences prefs;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FiSection(
      first: true,
      title: 'O que pesa na análise',
      hint: 'O perfil decide o yield que o sistema cobra de cada classe, e a ordem em que as '
          'oportunidades aparecem.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          FiRows(
            children: [
              FiDataRow(
                label: 'Perfil de risco',
                value: _riskProfileLabel(prefs.riskProfile),
                onTap: () => _pickRiskProfile(context, ref, prefs),
              ),
              FiDataRow(
                label: 'Nível de detalhe',
                value: _detailLevelLabel(prefs.detailLevel),
                detail: _detailLevelHints[prefs.detailLevel],
                onTap: () => _pickDetailLevel(context, ref, prefs),
              ),
              FiDataRow(
                label: 'Categorias preferidas',
                detail: prefs.preferredCategories.isEmpty
                    ? 'Nenhuma — todas pesam igual'
                    : prefs.preferredCategories.map(categoryLabel).join(', '),
                onTap: () => _pickPreferredCategories(context, ref, prefs),
              ),
              FiDataRow(
                label: 'Setores preferidos',
                detail: prefs.preferredSectors.isEmpty
                    ? 'Nenhum'
                    : prefs.preferredSectors.join(', '),
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
              FiDataRow(
                label: 'Ativos excluídos',
                detail: prefs.excludedTickers.isEmpty
                    ? 'Nenhum'
                    : prefs.excludedTickers.join(', '),
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
                        excludedTickers: values.map((v) => v.toUpperCase()).toList(),
                      ),
                ),
              ),
            ],
          ),
          const SizedBox(height: FiSpace.s5),
          FiFigures(
            figures: {
              'AÇÕES': formatPercent(prefs.desiredYieldStock * 100),
              'FIIS': formatPercent(prefs.desiredYieldFii * 100),
              'BDRS': formatPercent(prefs.desiredYieldBdr * 100),
              'ETFS': formatPercent(prefs.desiredYieldEtf * 100),
            },
          ),
          const SizedBox(height: FiSpace.s2),
          Text(
            'Yield desejado por classe — derivado do perfil, não editado aqui.',
            style: FiType.caption.copyWith(color: fiInk3(context)),
          ),
        ],
      ),
    );
  }
}

class FiGoals extends ConsumerWidget {
  const FiGoals({super.key, required this.prefs});

  final Preferences prefs;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final meses = prefs.reserveMonthsTarget;

    return FiSection(
      title: 'Metas',
      action: FiNavAction(
        label: 'Declarar metas',
        onPressed: () => context.go('/voce/objetivos'),
      ),
      child: FiRows(
        children: [
          FiDataRow(
            label: 'Renda passiva por mês',
            value: prefs.passiveIncomeGoal == null
                ? 'sem meta'
                : formatCurrency(prefs.passiveIncomeGoal),
            note: prefs.passiveIncomeGoal == null
                ? 'Sem alvo declarado o produto não inventa um.'
                : null,
          ),
          FiDataRow(
            label: 'Reserva de emergência',
            value: meses == null ? 'sem alvo' : '$meses ${meses == 1 ? 'mês' : 'meses'}',
            detail: meses == null
                ? 'Sem alvo declarado, a Sobra não mostra o passo da reserva.'
                : 'Medida contra o seu gasto fixo, e coberta pelo que você tem em '
                      'liquidez diária.',
            onTap: () => _pickReserveMonths(context, ref, prefs),
          ),
          const FiDataRow(
            label: 'Alocação por categoria e setor',
            detail: 'O alvo contra o qual a Sobra mede o desvio',
          ),
        ],
      ),
    );
  }
}

Future<void> _pickReserveMonths(
  BuildContext context,
  WidgetRef ref,
  Preferences prefs,
) async {
  final controller = TextEditingController(
    text: prefs.reserveMonthsTarget?.toString() ?? '',
  );

  final escolha = await showDialog<String>(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text('Reserva de emergência'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Quantos meses do seu gasto fixo você quer guardar. O produto não sugere um '
            'número: o seu custo de vida é que decide.',
            style: FiType.body.copyWith(color: fiInk2(context)),
          ),
          const SizedBox(height: FiSpace.s3),
          TextField(
            controller: controller,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Meses'),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, 'cancelar'),
          child: const Text('Cancelar'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, 'limpar'),
          child: const Text('Sem alvo'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(context, 'salvar'),
          child: const Text('Salvar'),
        ),
      ],
    ),
  );
  if (escolha == null || escolha == 'cancelar') return;

  final meses = int.tryParse(controller.text.trim());
  if (escolha == 'salvar' && (meses == null || meses < 0 || meses > 60)) return;

  await ref
      .read(apiRepositoryProvider)
      .savePreferences(
        passiveIncomeGoal: prefs.passiveIncomeGoal,
        reserveMonthsTarget: escolha == 'limpar' ? null : meses,
        clearReserveMonths: escolha == 'limpar',
      );
  ref.invalidate(preferencesProvider);
}

class FiNotifications extends ConsumerWidget {
  const FiNotifications({super.key, required this.prefs});

  final Preferences prefs;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FiSection(
      first: true,
      title: 'O que chega até você',
      child: FiRows(
        children: [
          FiDataRow(
            label: 'Alertas de preço',
            detail: 'Sempre imediato, é um alerta de risco',
            trailing: FiSwitch(
              label: 'Alertas de preço',
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
          ),
          FiDataRow(
            label: 'Resumo de oportunidades',
            value: _frequencyLabel(prefs.opportunitiesFrequency),
            onTap: () => _pickFrequency(context, ref, prefs),
          ),
        ],
      ),
    );
  }
}

class FiAppearance extends ConsumerWidget {
  const FiAppearance({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final escuro = ref.watch(themeModeProvider) == ThemeMode.dark;

    return FiSection(
      first: true,
      title: 'Aparência',
      child: FiDataRow(
        label: 'Tema escuro',
        detail: 'Fica neste aparelho — não viaja com a conta',
        trailing: FiSwitch(
          label: 'Tema escuro',
          value: escuro,
          onChanged: (_) => ref.read(themeModeProvider.notifier).toggle(),
        ),
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

const _detailLevelLabels = {
  'essencial': 'Essencial',
  'completo': 'Completo',
  'avancado': 'Avançado',
};

const _detailLevelHints = {
  'essencial': 'A etiqueta, a margem e o porquê; o método fica numa gaveta',
  'completo': 'Também as premissas, a confirmação e os indicadores',
  'avancado': 'Também os métodos, o silêncio de cada um e os insumos do cálculo',
};

String _detailLevelLabel(String value) => _detailLevelLabels[value] ?? value;

Future<void> _pickDetailLevel(
  BuildContext context,
  WidgetRef ref,
  Preferences prefs,
) async {
  final picked = await showDialog<String>(
    context: context,
    builder: (context) => SimpleDialog(
      title: const Text('Nível de detalhe'),
      children: [
        RadioGroup<String>(
          groupValue: prefs.detailLevel,
          onChanged: (v) => Navigator.pop(context, v),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: _detailLevelLabels.entries
                .map(
                  (e) => RadioListTile<String>(
                    value: e.key,
                    title: Text(e.value),
                    subtitle: Text(_detailLevelHints[e.key] ?? ''),
                  ),
                )
                .toList(),
          ),
        ),
      ],
    ),
  );
  if (picked == null || picked == prefs.detailLevel) return;

  await ref
      .read(apiRepositoryProvider)
      .savePreferences(passiveIncomeGoal: prefs.passiveIncomeGoal, detailLevel: picked);
  ref.invalidate(preferencesProvider);
}

const _preferenceCategories = [
  'acoes_br',
  'bdrs',
  'fiis',
  'etfs',
  'renda_fixa',
];

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
                .map(
                  (e) =>
                      RadioListTile<String>(value: e.key, title: Text(e.value)),
                )
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
                .map(
                  (e) =>
                      RadioListTile<String>(value: e.key, title: Text(e.value)),
                )
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
                  contentPadding: EdgeInsets.zero,
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

class FiReferral extends ConsumerWidget {
  const FiReferral({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final indicacao = ref.watch(referralProvider);

    return indicacao.when(
      loading: () => const FiSection(
        first: true,
        title: 'Indicação',
        child: FiSkeleton(shape: FiSkeletonShape.row, count: 2),
      ),
      error: (_, _) => const SizedBox.shrink(),
      data: (r) => FiSection(
        first: true,
        title: 'Indicação',
        hint: 'Quem entra pelo seu link ganha ${r.rewardDays} dias de Premium — e você '
            'também, quando essa pessoa salvar a primeira posição.',
        action: FiButton.secondary(
          label: 'Copiar link de indicação',
          icon: Icons.link,
          onPressed: () async {
            await Clipboard.setData(
              ClipboardData(text: 'https://fiance.app/?indicacao=${r.code}'),
            );
            if (context.mounted) {
              ScaffoldMessenger.of(
                context,
              ).showSnackBar(const SnackBar(content: Text('Link copiado')));
            }
          },
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              r.code,
              style: FiType.moneyLg.copyWith(color: fiInk1(context)),
            ),
            const SizedBox(height: FiSpace.s4),
            FiFigures(
              figures: {
                'CHEGARAM': '${r.attributed}',
                'MONTARAM CARTEIRA': '${r.qualified}',
                'DIAS GANHOS': '${r.daysEarned}',
              },
            ),
            if (r.pending > 0) ...[
              const SizedBox(height: FiSpace.s3),
              Text(
                '${r.pending} ainda não montaram carteira. O crédito sai quando elas '
                'salvarem a primeira posição.',
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class FiPriceAlerts extends ConsumerWidget {
  const FiPriceAlerts({super.key});

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
              const SizedBox(height: FiSpace.s4),
              DropdownButtonFormField<String>(
                initialValue: condition,
                decoration: const InputDecoration(labelText: 'Condição'),
                items: const [
                  DropdownMenuItem(value: 'below', child: Text('Abaixo de')),
                  DropdownMenuItem(value: 'above', child: Text('Acima de')),
                ],
                onChanged: (v) => setState(() => condition = v!),
              ),
              const SizedBox(height: FiSpace.s4),
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

    return FiSection(
      title: 'Alertas de preço',
      count: alerts.valueOrNull?.length,
      action: FiButton.secondary(
        label: 'Novo alerta',
        icon: Icons.add,
        onPressed: () => _createAlert(context, ref),
      ),
      child: alerts.when(
        loading: () => const FiSkeleton(shape: FiSkeletonShape.row, count: 2),
        error: (err, _) => FiErrorState(
          error: err,
          action: 'carregar seus alertas',
          onRetry: () => ref.invalidate(alertsProvider),
        ),
        data: (items) {
          if (items.isEmpty) {
            return const FiEmptyLine(
              'Nenhum alerta. Um alerta dispara quando o preço cruza o valor que você '
              'declarou — é a condição, não o palpite.',
            );
          }
          return FiRows(
            children: [
              for (final a in items)
                FiDataRow(
                  label: a.ticker,
                  detail:
                      '${a.condition == 'below' ? 'Abaixo de' : 'Acima de'} '
                      '${formatCurrency(a.targetPrice)}'
                      '${a.triggeredAt != null ? ' · disparado' : ''}',
                  trailing: IconButton(
                    icon: const Icon(Icons.delete_outline),
                    tooltip: 'Apagar alerta de ${a.ticker}',
                    onPressed: () async {
                      await ref.read(apiRepositoryProvider).deleteAlert(a.id);
                      ref.invalidate(alertsProvider);
                    },
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class FiLegal extends StatelessWidget {
  const FiLegal({super.key});

  @override
  Widget build(BuildContext context) {
    return FiSection(
      title: 'Termos e privacidade',
      child: FiRows(
        children: const [
          _LegalRow(label: 'Termos de Uso', url: termsUrl),
          _LegalRow(
            label: 'Política de Privacidade',
            detail: 'Que dado guardamos, e como você o leva embora',
            url: privacyUrl,
          ),
          _LegalRow(
            label: 'Aviso CVM',
            detail: 'Por que a análise não é recomendação',
            url: cvmNoticeUrl,
          ),
        ],
      ),
    );
  }
}

class _LegalRow extends StatelessWidget {
  const _LegalRow({required this.label, required this.url, this.detail});

  final String label;
  final String? detail;
  final String url;

  @override
  Widget build(BuildContext context) {
    return FiDataRow(
      label: label,
      detail: detail,
      trailing: Icon(Icons.open_in_new, size: 16, color: fiInk3(context)),
      onTap: () async {
        final abriu = await openInBrowser(url);
        if (!abriu && context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Não foi possível abrir $url')),
          );
        }
      },
    );
  }
}

class FiAccount extends ConsumerWidget {
  const FiAccount({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FiSection(
      title: 'Conta',
      action: FiButton.danger(
        label: 'Sair desta conta',
        onPressed: () async {
          await ref.read(notificationsServiceProvider).unregisterToken();
          await ref.read(authServiceProvider).signOut();
          ref.read(currentUserProvider.notifier).state = null;
          if (context.mounted) context.go('/login');
        },
      ),
      child: FiRows(
        children: [
          FiDataRow(
            label: 'Baixar meus dados',
            detail: 'Tudo o que esta conta guarda, em JSON',
            trailing: Icon(Icons.download, size: 16, color: fiInk3(context)),
            onTap: () => exportAccountData(context, ref),
          ),
          FiDataRow(
            label: 'Excluir esta conta',
            detail: 'Apaga tudo, e não há como desfazer',
            onTap: () => context.go('/voce/conta/excluir'),
          ),
        ],
      ),
    );
  }
}
