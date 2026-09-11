import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/widgets/empty_state.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import 'widgets/feed_tiles.dart';

class AtividadeScreen extends ConsumerWidget {
  const AtividadeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(whatsNewProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('O que aconteceu')),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(whatsNewProvider),
        child: async.when(
          loading: () => FiSkeleton.tela(
            shape: FiSkeletonShape.row,
            count: 6,
            label: 'Carregando a atividade',
          ),
          error: (err, _) => FiErrorState(
            error: err,
            action: 'carregar a atividade',
            onRetry: () => ref.invalidate(whatsNewProvider),
          ),
          data: (data) {
            if (data.items.isEmpty) {
              return ListView(
                children: const [
                  FiEmptyState(
                    title: 'Nada mudou desde a sua última visita',
                    body: 'Silêncio aqui é boa notícia, e não falha de carregamento: nenhum '
                        'veredito virou, nenhuma meta se afastou e nada venceu.',
                  ),
                ],
              );
            }

            return ListView(
              padding: const EdgeInsets.fromLTRB(
                FiLayout.gutter,
                FiSpace.s3,
                FiLayout.gutter,
                FiLayout.scrollTail,
              ),
              children: [
                Text(
                  'Mudanças de veredito, desvios de meta, vencimentos e proventos — do mais '
                  'recente para o mais antigo.',
                  style: FiType.body.copyWith(color: fiInk2(context)),
                ),
                const SizedBox(height: FiSpace.s5),
                ...data.items.map((item) => FiWhatsNewTile(item: item)),
              ],
            );
          },
        ),
      ),
    );
  }
}
