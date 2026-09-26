import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';

class _Step {
  const _Step({required this.number, required this.title, required this.body});

  final int number;
  final String title;
  final String body;
}

const _steps = [
  _Step(
    number: 1,
    title: 'Sua conta está pronta',
    body: 'Nenhum passo é obrigatório: o aplicativo funciona a partir de agora. Os próximos só '
        'destravam as leituras que dependem do que você declarar.',
  ),
  _Step(
    number: 2,
    title: 'Registre sua carteira',
    body: 'Traga o extrato da corretora de uma vez, registre uma compra no razão ou cadastre uma '
        'renda fixa. Com a carteira, o patrimônio, o imposto e o risco passam a existir.',
  ),
  _Step(
    number: 3,
    title: 'Declare uma meta de alocação',
    body: 'Uma meta basta. É ela que transforma "como estou" em "o que faço": sem meta '
        'declarada, nada aponta desvio.',
  ),
];

class OnboardingScreen extends ConsumerWidget {
  const OnboardingScreen({super.key, this.step});

  final int? step;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final estado = ref.watch(onboardingProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Primeiros passos')),
      body: estado.when(
        loading: () => FiSkeleton.screen(
          shape: FiSkeletonShape.row,
          count: 3,
          label: 'Lendo o que você já fez',
        ),
        error: (err, _) => FiErrorState(
          error: err,
          title: 'Não conseguimos ler os seus primeiros passos',
          action: 'ler os primeiros passos',
          onRetry: () => ref.invalidate(onboardingProvider),
        ),
        data: (data) => _Steps(state: data, focus: step),
      ),
    );
  }
}

class _Steps extends ConsumerStatefulWidget {
  const _Steps({required this.state, this.focus});

  final OnboardingState state;
  final int? focus;

  @override
  ConsumerState<_Steps> createState() => _StepsState();
}

class _StepsState extends ConsumerState<_Steps> {
  bool _finishing = false;

  bool _done(int number) => switch (number) {
    1 => true,
    2 => widget.state.step > 2,
    _ => widget.state.hasGoals,
  };

  Future<void> _finish({required bool skipped}) async {
    setState(() => _finishing = true);
    try {
      await ref.read(apiRepositoryProvider).completeOnboarding(skipped: skipped);
      if (!mounted) return;
      ref.invalidate(onboardingProvider);
      context.go('/mes');
    } catch (e) {
      if (!mounted) return;
      setState(() => _finishing = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(fiErrorMessage(e, action: 'concluir os primeiros passos'))),
      );
    }
  }

  List<Widget> _actions(int number) => switch (number) {
    2 => [
      FiButton.primary(
        label: 'Importar extrato',
        icon: Icons.upload_file_outlined,
        onPressed: () => context.push('/patrimonio/razao/importar'),
      ),
      FiButton.secondary(
        label: 'Abrir o livro-razão',
        onPressed: () => context.push('/patrimonio/razao'),
      ),
    ],
    3 => [
      FiButton.primary(
        label: 'Definir metas',
        icon: Icons.flag_outlined,
        onPressed: () => context.push('/voce/objetivos'),
      ),
    ],
    _ => const [],
  };

  @override
  Widget build(BuildContext context) {
    final s = widget.state;
    final foco = (widget.focus != null && widget.focus! >= 1 && widget.focus! <= _steps.length)
        ? widget.focus!
        : s.step;
    final tudoFeito = _steps.every((p) => _done(p.number));

    return ListView(
      padding: const EdgeInsets.fromLTRB(
        FiLayout.gutter,
        FiSpace.s3,
        FiLayout.gutter,
        FiSpace.s8,
      ),
      children: [
        Text(
          s.completed ? 'Você já passou por aqui' : 'Três passos, e nenhum trava o resto',
          style: FiType.title.copyWith(color: fiInk1(context)),
        ),
        const SizedBox(height: FiSpace.s2),
        Text(
          tudoFeito ? 'Tudo pronto: carteira registrada e meta declarada.' : s.reason,
          style: FiType.body.copyWith(color: fiInk2(context)),
        ),
        const SizedBox(height: FiSpace.s5),
        for (final passo in _steps)
          Padding(
            padding: const EdgeInsets.only(bottom: FiSpace.s3),
            child: FiObject(
              accent: passo.number == foco && !_done(passo.number)
                  ? fiStateColor(FiState.attention, Theme.of(context).brightness)
                  : null,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'Passo ${passo.number} de ${_steps.length}',
                          style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                        ),
                      ),
                      _done(passo.number)
                          ? const FiTag(label: 'Feito', state: FiState.favorable)
                          : const FiTag(label: 'Falta', state: FiState.neutral),
                    ],
                  ),
                  const SizedBox(height: FiSpace.s2),
                  Text(passo.title, style: FiType.title.copyWith(color: fiInk1(context))),
                  const SizedBox(height: FiSpace.s1),
                  Text(passo.body, style: FiType.body.copyWith(color: fiInk2(context))),
                  if (!_done(passo.number) && _actions(passo.number).isNotEmpty) ...[
                    const SizedBox(height: FiSpace.s3),
                    Wrap(
                      spacing: FiSpace.s2,
                      runSpacing: FiSpace.s2,
                      children: _actions(passo.number),
                    ),
                  ],
                ],
              ),
            ),
          ),
        if (!s.completed) ...[
          const SizedBox(height: FiSpace.s3),
          tudoFeito
              ? FiButton.primary(
                  label: 'Concluir',
                  expand: true,
                  busy: _finishing,
                  onPressed: _finishing ? null : () => _finish(skipped: false),
                )
              : FiButton.quiet(
                  label: 'Pular por agora',
                  expand: true,
                  busy: _finishing,
                  onPressed: _finishing ? null : () => _finish(skipped: true),
                ),
        ],
      ],
    );
  }
}
