import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// A busca global, alcançável de qualquer destino — como o ⌘K do web.
///
/// Ela existia desde sempre em `/busca` e tinha **uma** porta: a barra de `/mes/feed`, que é
/// tela secundária de um destino só. Achar um ativo exigia saber onde a porta estava.
class FiSearchAction extends StatelessWidget {
  const FiSearchAction({super.key});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.search),
      tooltip: 'Buscar ativo, título ou tela',
      onPressed: () => context.push('/busca'),
    );
  }
}
