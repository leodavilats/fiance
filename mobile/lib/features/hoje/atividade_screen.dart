import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/design_tokens.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import 'widgets/hoje_tiles.dart';

class AtividadeScreen extends ConsumerWidget {
  const AtividadeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(whatsNewProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final ink2 = isDark ? FiColors.darkInk2 : FiColors.lightInk2;

    return Scaffold(
      appBar: AppBar(title: const Text('O que aconteceu')),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(whatsNewProvider),
        child: async.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => Padding(
            padding: const EdgeInsets.all(FiSpace.s4),
            child: FiErrorState(error: err, action: 'carregar a atividade'),
          ),
          data: (data) {
            if (data.items.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(FiSpace.s4),
                children: [
                  Text(
                    'Nada mudou desde a sua última visita. Silêncio aqui é boa '
                    'notícia — não é falha de carregamento.',
                    style: FiType.body.copyWith(color: ink2),
                  ),
                ],
              );
            }

            return ListView(
              padding: const EdgeInsets.all(FiSpace.s4),
              children: [
                Text(
                  'Mudanças de veredito, desvios de meta, vencimentos e '
                  'proventos — do mais recente para o mais antigo.',
                  style: FiType.body.copyWith(color: ink2),
                ),
                const SizedBox(height: FiSpace.s4),
                ...data.items.map((item) => FiWhatsNewTile(item: item)),
              ],
            );
          },
        ),
      ),
    );
  }
}
