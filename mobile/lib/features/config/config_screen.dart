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
import '../../core/sector_translations.dart';
import '../../core/theme.dart';
import '../../core/theme_provider.dart';
import '../../core/vocabulary.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/feedback.dart';
import 'delete_account_screen.dart';
import '../../core/widgets/controls.dart';

class ConfigScreen extends ConsumerWidget {
  const ConfigScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final preferences = ref.watch(preferencesProvider);
    final alertas = ref.watch(alertsProvider);
    final escuro = ref.watch(themeModeProvider) == ThemeMode.dark;
    final passos = ref.watch(onboardingProvider);

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
                label: 'Primeiros passos',
                detail: passos.maybeWhen(
                  data: (s) => s.completed
                      ? 'Concluídos — reveja quando quiser'
                      : 'Passo ${s.step} de ${s.totalSteps} · ${s.reason}',
                  orElse: () => 'Carteira e meta, e nada trava o resto',
                ),
                onTap: () => context.go('/voce/comecar'),
              ),
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
                    : prefs.preferredSectors.map(translateSector).toSet().join(', '),
                onTap: () => _pickPreferredSectors(context, ref, prefs),
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
                  invalid: _tickerInvalido,
                  action: 'salvar os ativos excluídos',
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
            onTap: () => context.go('/voce/objetivos'),
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
          FiDataRow(
            label: 'Alocação por categoria e setor',
            detail: 'O alvo contra o qual a Sobra mede o desvio',
            onTap: () => context.go('/voce/objetivos'),
          ),
        ],
      ),
    );
  }
}

Future<void> _savePreferences(
  BuildContext context,
  WidgetRef ref,
  Future<void> Function() write, {
  required String action,
  String? success,
}) async {
  if (!context.mounted) return;
  final ok = await fiAttempt(context, write, action: action, success: success);
  if (!ok) return;
  ref.invalidate(preferencesProvider);
  ref.invalidate(opportunitiesProvider);
  invalidateAllocationReaders(ref);
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
    builder: (context) => ValueListenableBuilder<TextEditingValue>(
      valueListenable: controller,
      builder: (context, digitado, _) {
        final texto = digitado.text.trim();
        final meses = int.tryParse(texto);
        final valido = meses != null && meses >= 0 && meses <= 60;
        return AlertDialog(
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
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                decoration: InputDecoration(
                  labelText: 'Meses',
                  errorText: texto.isEmpty || valido ? null : 'Use um número de 0 a 60',
                ),
              ),
            ],
          ),
          actions: [
            FiButton.quiet(
              label: 'Cancelar',
              onPressed: () => Navigator.pop(context, 'cancelar'),
            ),
            FiButton.quiet(
              label: 'Sem alvo',
              onPressed: () => Navigator.pop(context, 'limpar'),
            ),
            FiButton.primary(
              label: 'Salvar',
              onPressed: valido ? () => Navigator.pop(context, 'salvar') : null,
            ),
          ],
        );
      },
    ),
  );
  if (escolha == null || escolha == 'cancelar') return;

  final limpar = escolha == 'limpar';
  final meses = int.tryParse(controller.text.trim());
  if (!limpar && (meses == null || meses < 0 || meses > 60)) return;
  if (!context.mounted) return;

  await _savePreferences(
    context,
    ref,
    () => ref
        .read(apiRepositoryProvider)
        .savePreferences(
          passiveIncomeGoal: prefs.passiveIncomeGoal,
          reserveMonthsTarget: limpar ? null : meses,
          clearReserveMonths: limpar,
        ),
    action: 'salvar a reserva de emergência',
  );
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
            trailing: _PriceAlertsSwitch(prefs: prefs),
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

class _PriceAlertsSwitch extends ConsumerStatefulWidget {
  const _PriceAlertsSwitch({required this.prefs});

  final Preferences prefs;

  @override
  ConsumerState<_PriceAlertsSwitch> createState() => _PriceAlertsSwitchState();
}

class _PriceAlertsSwitchState extends ConsumerState<_PriceAlertsSwitch> {
  bool? _pedido;

  Future<void> _mudar(bool v) async {
    setState(() => _pedido = v);
    final ok = await fiAttempt(
      context,
      () => ref
          .read(apiRepositoryProvider)
          .savePreferences(
            passiveIncomeGoal: widget.prefs.passiveIncomeGoal,
            notifyPriceAlerts: v,
          ),
      action: v ? 'ligar os alertas de preço' : 'desligar os alertas de preço',
    );
    if (ok) ref.invalidate(preferencesProvider);
    if (mounted) setState(() => _pedido = null);
  }

  @override
  Widget build(BuildContext context) {
    final salvando = _pedido != null;
    return FiSwitch(
      label: 'Alertas de preço',
      value: _pedido ?? widget.prefs.notifyPriceAlerts,
      onChanged: salvando ? null : _mudar,
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
  if (picked == null || picked == prefs.detailLevel || !context.mounted) return;

  await _savePreferences(
    context,
    ref,
    () => ref
        .read(apiRepositoryProvider)
        .savePreferences(passiveIncomeGoal: prefs.passiveIncomeGoal, detailLevel: picked),
    action: 'salvar o nível de detalhe',
  );
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
  if (picked == null || picked == prefs.opportunitiesFrequency || !context.mounted) return;

  await _savePreferences(
    context,
    ref,
    () => ref
        .read(apiRepositoryProvider)
        .savePreferences(
          passiveIncomeGoal: prefs.passiveIncomeGoal,
          opportunitiesFrequency: picked,
        ),
    action: 'salvar a cadência do resumo',
  );
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
  if (picked == null || picked == prefs.riskProfile || !context.mounted) return;

  await _savePreferences(
    context,
    ref,
    () => ref
        .read(apiRepositoryProvider)
        .savePreferences(
          passiveIncomeGoal: prefs.passiveIncomeGoal,
          riskProfile: picked,
        ),
    action: 'salvar o perfil de risco',
  );
}

Future<List<String>?> _pickMany(
  BuildContext context, {
  required String title,
  required List<String> options,
  required Iterable<String> initial,
  String Function(String option)? label,
}) async {
  final selected = {...initial};

  final confirmed = await showDialog<bool>(
    context: context,
    builder: (context) => StatefulBuilder(
      builder: (context, setState) => AlertDialog(
        title: Text(title),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: options
                .map(
                  (c) => CheckboxListTile(
                    value: selected.contains(c),
                    title: Text(label == null ? c : label(c)),
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
        ),
        actions: [
          FiButton.quiet(
            label: 'Cancelar',
            onPressed: () => Navigator.pop(context, false),
          ),
          FiButton.primary(
            label: 'Salvar',
            onPressed: () => Navigator.pop(context, true),
          ),
        ],
      ),
    ),
  );
  if (confirmed != true) return null;
  return [for (final o in options) if (selected.contains(o)) o];
}

Future<void> _pickPreferredCategories(
  BuildContext context,
  WidgetRef ref,
  Preferences prefs,
) async {
  final selected = await _pickMany(
    context,
    title: 'Categorias preferidas',
    options: _preferenceCategories,
    initial: prefs.preferredCategories,
    label: categoryLabel,
  );
  if (selected == null || !context.mounted) return;

  await _savePreferences(
    context,
    ref,
    () => ref
        .read(apiRepositoryProvider)
        .savePreferences(
          passiveIncomeGoal: prefs.passiveIncomeGoal,
          preferredCategories: selected,
        ),
    action: 'salvar as categorias preferidas',
  );
}

Future<void> _pickPreferredSectors(
  BuildContext context,
  WidgetRef ref,
  Preferences prefs,
) async {
  final selected = await _pickMany(
    context,
    title: 'Setores preferidos',
    options: fiSectors.values.toSet().toList()..sort(),
    initial: prefs.preferredSectors.map(translateSector),
  );
  if (selected == null || !context.mounted) return;

  await _savePreferences(
    context,
    ref,
    () => ref
        .read(apiRepositoryProvider)
        .savePreferences(
          passiveIncomeGoal: prefs.passiveIncomeGoal,
          preferredSectors: selected,
        ),
    action: 'salvar os setores preferidos',
  );
}

Future<void> _editCsvList(
  BuildContext context,
  WidgetRef ref,
  Preferences prefs, {
  required String title,
  required String hint,
  required List<String> initial,
  required Future<void> Function(List<String> values) apply,
  required String action,
  String? Function(String item)? invalid,
}) async {
  final controller = TextEditingController(text: initial.join(', '));

  List<String> separar(String texto) =>
      texto.split(',').map((v) => v.trim()).where((v) => v.isNotEmpty).toList();

  final confirmed = await showDialog<bool>(
    context: context,
    builder: (context) => ValueListenableBuilder<TextEditingValue>(
      valueListenable: controller,
      builder: (context, digitado, _) {
        String? erro;
        if (invalid != null) {
          for (final item in separar(digitado.text)) {
            erro = invalid(item);
            if (erro != null) break;
          }
        }
        return AlertDialog(
          title: Text(title),
          content: TextField(
            controller: controller,
            decoration: InputDecoration(hintText: hint, errorText: erro, errorMaxLines: 2),
          ),
          actions: [
            FiButton.quiet(
              label: 'Cancelar',
              onPressed: () => Navigator.pop(context, false),
            ),
            FiButton.primary(
              label: 'Salvar',
              onPressed: erro == null ? () => Navigator.pop(context, true) : null,
            ),
          ],
        );
      },
    ),
  );
  if (confirmed != true || !context.mounted) return;

  await _savePreferences(context, ref, () => apply(separar(controller.text)), action: action);
}

String? _tickerInvalido(String item) =>
    RegExp(r'^[A-Z][A-Z0-9]{3}\d{1,2}$').hasMatch(item.toUpperCase())
        ? null
        : '"$item" não é um código da B3, como PETR4';

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
      error: (err, _) => FiSection(
        first: true,
        title: 'Indicação',
        child: FiErrorState(
          error: err,
          action: 'carregar sua indicação',
          onRetry: () => ref.invalidate(referralProvider),
        ),
      ),
      data: (r) => FiSection(
        first: true,
        title: 'Indicação',
        hint: r.rewardDays > 0
            ? 'Quem entra pelo seu link ganha ${r.rewardDays} dias de Premium — e você '
                  'também, quando essa pessoa salvar a primeira posição.'
            : 'Mande o seu link para quem quiser organizar o dinheiro do mesmo jeito. Aqui '
                  'você acompanha quem chegou por ele.',
        action: FiButton.secondary(
          label: 'Copiar link de indicação',
          icon: Icons.link,
          onPressed: () async {
            await Clipboard.setData(
              ClipboardData(text: 'https://fiance.app/?indicacao=${r.code}'),
            );
            if (context.mounted) fiNotify(context, 'Link copiado');
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
                if (r.rewardDays > 0 || r.daysEarned > 0) 'DIAS GANHOS': '${r.daysEarned}',
              },
            ),
            if (r.pending > 0) ...[
              const SizedBox(height: FiSpace.s3),
              Text(
                r.rewardDays > 0
                    ? '${r.pending} ainda não montaram carteira. O crédito sai quando elas '
                          'salvarem a primeira posição.'
                    : '${r.pending} ainda não montaram carteira.',
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class FiPriceAlerts extends ConsumerStatefulWidget {
  const FiPriceAlerts({super.key});

  @override
  ConsumerState<FiPriceAlerts> createState() => _FiPriceAlertsState();
}

class _FiPriceAlertsState extends ConsumerState<FiPriceAlerts> {
  bool _criando = false;
  final _apagando = <int>{};

  Future<void> _createAlert() async {
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
              ValueListenableBuilder<TextEditingValue>(
                valueListenable: priceCtrl,
                builder: (context, digitado, _) {
                  final texto = digitado.text.trim();
                  final preco = parseDecimal(texto);
                  return TextField(
                    controller: priceCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: InputDecoration(
                      labelText: 'Preço alvo (R\$)',
                      errorText: texto.isEmpty || (preco != null && preco > 0)
                          ? null
                          : 'Use um preço maior que zero, como 38,50',
                    ),
                  );
                },
              ),
            ],
          ),
          actions: [
            FiButton.quiet(
              label: 'Cancelar',
              onPressed: () => Navigator.pop(context, false),
            ),
            ListenableBuilder(
              listenable: Listenable.merge([tickerCtrl, priceCtrl]),
              builder: (context, _) {
                final preco = parseDecimal(priceCtrl.text.trim());
                final valido =
                    tickerCtrl.text.trim().isNotEmpty && preco != null && preco > 0;
                return FiButton.primary(
                  label: 'Criar',
                  onPressed: valido ? () => Navigator.pop(context, true) : null,
                );
              },
            ),
          ],
        ),
      ),
    );

    if (confirmed != true || !mounted) return;
    final ticker = tickerCtrl.text.trim().toUpperCase();
    final price = parseDecimal(priceCtrl.text.trim());
    if (ticker.isEmpty || price == null || price <= 0) return;

    setState(() => _criando = true);
    final ok = await fiAttempt(
      context,
      () => ref
          .read(apiRepositoryProvider)
          .createAlert(ticker: ticker, condition: condition, targetPrice: price),
      action: 'criar o alerta',
      success: 'Alerta de $ticker criado',
    );
    if (ok) ref.invalidate(alertsProvider);
    if (mounted) setState(() => _criando = false);
  }

  Future<void> _deleteAlert(PriceAlert a) async {
    final confirmado = await fiConfirm(
      context,
      title: 'Apagar o alerta de ${a.ticker}?',
      body: 'O aviso de ${a.condition == 'below' ? 'abaixo de' : 'acima de'} '
          '${formatCurrency(a.targetPrice)} deixa de chegar.',
      confirmLabel: 'Apagar',
    );
    if (!confirmado || !mounted) return;

    setState(() => _apagando.add(a.id));
    final ok = await fiAttempt(
      context,
      () => ref.read(apiRepositoryProvider).deleteAlert(a.id),
      action: 'apagar o alerta',
      success: 'Alerta de ${a.ticker} apagado',
    );
    if (ok) ref.invalidate(alertsProvider);
    if (mounted) setState(() => _apagando.remove(a.id));
  }

  @override
  Widget build(BuildContext context) {
    final alerts = ref.watch(alertsProvider);

    return FiSection(
      title: 'Alertas de preço',
      count: alerts.valueOrNull?.length,
      action: FiButton.secondary(
        label: 'Novo alerta',
        icon: Icons.add,
        busy: _criando,
        onPressed: _criando ? null : _createAlert,
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
                    onPressed: _apagando.contains(a.id) ? null : () => _deleteAlert(a),
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
      chevron: false,
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

class FiAccount extends ConsumerStatefulWidget {
  const FiAccount({super.key});

  @override
  ConsumerState<FiAccount> createState() => _FiAccountState();
}

class _FiAccountState extends ConsumerState<FiAccount> {
  bool _saindo = false;
  bool _exportando = false;

  Future<void> _exportar() async {
    setState(() => _exportando = true);
    await exportAccountData(context, ref);
    if (mounted) setState(() => _exportando = false);
  }

  Future<void> _sair() async {
    final confirmado = await fiConfirm(
      context,
      title: 'Sair desta conta?',
      body: 'Seus dados continuam guardados na conta. Neste aparelho, você entra de novo com o '
          'Google, e os avisos deixam de chegar aqui até lá.',
      confirmLabel: 'Sair',
      destructive: false,
    );
    if (!confirmado || !mounted) return;

    final roteador = GoRouter.of(context);
    setState(() => _saindo = true);
    try {
      await ref.read(signOutProvider)();
    } catch (_) {
    } finally {
      roteador.go('/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return FiSection(
      title: 'Conta',
      action: FiButton.danger(
        label: 'Sair desta conta',
        busy: _saindo,
        onPressed: _saindo ? null : _sair,
      ),
      child: FiRows(
        children: [
          FiDataRow(
            label: 'Baixar meus dados',
            detail: _exportando
                ? 'Preparando o arquivo…'
                : 'Tudo o que esta conta guarda, em JSON',
            trailing: Icon(Icons.download, size: 16, color: fiInk3(context)),
            chevron: false,
            onTap: _exportando ? null : _exportar,
          ),
          FiDataRow(
            label: 'Importar meus dados',
            detail: 'Traz de volta um arquivo baixado daqui, para uma conta sem dados',
            onTap: () => context.go('/voce/conta/importar'),
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
