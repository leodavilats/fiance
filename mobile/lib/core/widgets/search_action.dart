import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

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
