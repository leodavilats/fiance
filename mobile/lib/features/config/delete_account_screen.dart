import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:share_plus/share_plus.dart';

import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';

Future<void> exportAccountData(BuildContext context, WidgetRef ref) async {
  final mensageiro = ScaffoldMessenger.of(context);

  try {
    final export = await ref.read(apiRepositoryProvider).exportAccount();
    await SharePlus.instance.share(
      ShareParams(
        files: [
          XFile.fromData(
            Uint8List.fromList(export.bytes),
            mimeType: 'application/json',
            name: export.filename,
          ),
        ],
        fileNameOverrides: [export.filename],
        subject: 'Meus dados no fiance',
      ),
    );
  } catch (e) {
    mensageiro.showSnackBar(
      SnackBar(content: Text(fiErrorMessage(e, action: 'preparar seus dados'))),
    );
  }
}

class DeleteAccountScreen extends ConsumerWidget {
  const DeleteAccountScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final policy = ref.watch(deletionPolicyProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Excluir conta')),
      body: policy.when(
        loading: () => FiSkeleton.screen(count: 4),
        error: (err, _) => FiErrorState(
          error: err,
          action: 'carregar o que a exclusão apaga',
          onRetry: () => ref.invalidate(deletionPolicyProvider),
        ),
        data: (p) => _Corpo(policy: p),
      ),
    );
  }
}

class _Corpo extends ConsumerStatefulWidget {
  const _Corpo({required this.policy});

  final AccountDeletionPolicy policy;

  @override
  ConsumerState<_Corpo> createState() => _CorpoState();
}

class _CorpoState extends ConsumerState<_Corpo> {
  final _confirmation = TextEditingController();
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _confirmation.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _confirmation.dispose();
    super.dispose();
  }

  bool get _confirmed =>
      _confirmation.text.trim().toUpperCase() == widget.policy.confirmationPhrase.toUpperCase();

  Future<void> _delete() async {
    final router = GoRouter.of(context);
    final mensageiro = ScaffoldMessenger.of(context);

    setState(() => _busy = true);
    try {
      await ref.read(apiRepositoryProvider).deleteAccount(widget.policy.confirmationPhrase);
      await ref.read(authServiceProvider).signOut();
      ref.read(currentUserProvider.notifier).state = null;
      router.go('/login');
      mensageiro.showSnackBar(
        const SnackBar(content: Text('Conta excluída. Os dados saíram do banco.')),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      mensageiro.showSnackBar(
        SnackBar(content: Text(fiErrorMessage(e, action: 'excluir sua conta'))),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.policy;
    final apagado = p.removes.map(accountDataLabel).join(', ');

    return ListView(
      padding: const EdgeInsets.fromLTRB(
        FiLayout.gutter,
        FiSpace.s2,
        FiLayout.gutter,
        FiLayout.scrollTail,
      ),
      children: [
        FiSection(
          first: true,
          title: 'O que é apagado',
          hint: 'Não há como desfazer.',
          child: Text(
            '${p.removes.length} conjuntos de dados: $apagado.',
            style: FiType.body.copyWith(color: fiInk2(context)),
          ),
        ),
        FiSection(
          title: 'O que ainda existe por até ${p.slaDays} dias',
          child: Text(
            p.note,
            style: FiType.body.copyWith(color: fiInk2(context)),
          ),
        ),
        FiSection(
          title: 'Antes de excluir',
          hint: 'A exportação sai em JSON, com tudo o que a conta guarda.',
          child: FiButton.secondary(
            label: 'Baixar meus dados',
            icon: Icons.download,
            onPressed: () => exportAccountData(context, ref),
          ),
        ),
        FiSection(
          title: 'Confirmar',
          hint: 'Digite ${p.confirmationPhrase} para liberar o botão.',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextField(
                controller: _confirmation,
                autocorrect: false,
                textCapitalization: TextCapitalization.characters,
                decoration: const InputDecoration(labelText: 'Confirmação'),
              ),
              const SizedBox(height: FiSpace.s4),
              FiButton.danger(
                label: 'Excluir minha conta',
                expand: true,
                busy: _busy,
                onPressed: _confirmed ? _delete : null,
              ),
            ],
          ),
        ),
      ],
    );
  }
}
