import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/search_action.dart';
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

/// A ordem e a do que muda o julgamento do produto: o que pesa na analise, o que chega como
/// aviso, o aparelho, e por ultimo a conta.
class ConfigScreen extends ConsumerWidget {
  const ConfigScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final preferences = ref.watch(preferencesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Você'),
        actions: const [FiSearchAction()],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          FiLayout.scrollTail,
        ),
        children: [
          const _Identidade(),

          preferences.when(
            loading: () => const Padding(
              padding: EdgeInsets.only(top: FiSpace.s8),
              child: FiSkeleton(shape: FiSkeletonShape.row, count: 6),
            ),
            error: (err, _) => Padding(
              padding: const EdgeInsets.only(top: FiSpace.s6),
              child: FiErrorState(
                error: err,
                action: 'carregar suas preferências',
                onRetry: () => ref.invalidate(preferencesProvider),
              ),
            ),
            data: (prefs) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _Recomendacao(prefs: prefs),
                _Metas(prefs: prefs),
                _Notificacoes(prefs: prefs),
              ],
            ),
          ),

          const _Alertas(),
          const _Indicacao(),
          const _Aparencia(),
          const _Legal(),
          const _Conta(),
        ],
      ),
    );
  }
}

class _Identidade extends ConsumerWidget {
  const _Identidade();

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

/// Os `yield` desejados nao sao ajuste: vem do servidor, derivados do perfil, e por isso saem
/// como cifra e nao como linha com seta.
class _Recomendacao extends ConsumerWidget {
  const _Recomendacao({required this.prefs});

  final Preferences prefs;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FiSection(
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

class _Metas extends StatelessWidget {
  const _Metas({required this.prefs});

  final Preferences prefs;

  @override
  Widget build(BuildContext context) {
    return FiSection(
      title: 'Metas',
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
            label: 'Alocação por categoria',
            detail: 'O alvo contra o qual a Sobra mede o desvio',
            onTap: () => context.go('/voce/objetivos'),
          ),
        ],
      ),
    );
  }
}

class _Notificacoes extends ConsumerWidget {
  const _Notificacoes({required this.prefs});

  final Preferences prefs;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FiSection(
      title: 'O que chega até você',
      child: FiRows(
        children: [
          FiDataRow(
            label: 'Alertas de preço',
            detail: 'Sempre imediato, é um alerta de risco',
            trailing: Switch(
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

class _Aparencia extends ConsumerWidget {
  const _Aparencia();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final escuro = ref.watch(themeModeProvider) == ThemeMode.dark;

    return FiSection(
      title: 'Aparência',
      child: FiDataRow(
        label: 'Tema escuro',
        detail: 'Fica neste aparelho — não viaja com a conta',
        trailing: Switch(
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

class _Indicacao extends ConsumerWidget {
  const _Indicacao();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final indicacao = ref.watch(referralProvider);

    return indicacao.when(
      loading: () => const SizedBox.shrink(),
      error: (_, _) => const SizedBox.shrink(),
      data: (r) => FiSection(
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

class _Alertas extends ConsumerWidget {
  const _Alertas();

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

class _Legal extends StatelessWidget {
  const _Legal();

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
        final abriu = await abrirNoNavegador(url);
        if (!abriu && context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Não foi possível abrir $url')),
          );
        }
      },
    );
  }
}

class _Conta extends ConsumerWidget {
  const _Conta();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FiSection(
      title: 'Conta',
      child: FiButton.danger(
        label: 'Sair desta conta',
        onPressed: () async {
          await ref.read(notificationsServiceProvider).unregisterToken();
          await ref.read(authServiceProvider).signOut();
          ref.read(currentUserProvider.notifier).state = null;
          if (context.mounted) context.go('/login');
        },
      ),
    );
  }
}
