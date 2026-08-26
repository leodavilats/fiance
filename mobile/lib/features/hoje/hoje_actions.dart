import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Para onde cada ação sugerida pelo backend leva.
///
/// Vivia como `static` dentro de `DashboardScreen`, o que obrigava todo widget
/// filho a importar a tela inteira só para navegar. E apontava para as rotas
/// antigas (`/assets`, `/market`, `/config`), que hoje só existem como
/// redirect — funcionava por acidente, com um salto a mais em cada toque.
void runHojeAction(BuildContext context, String? action, String? ticker) {
  switch (action) {
    case 'analyze':
      context.go(ticker != null ? '/ativo/$ticker' : '/carteira');
    case 'sell':
      context.go('/carteira');
    case 'fixed_income':
      context.go('/carteira/renda-fixa');
    case 'goals':
      context.go('/estrategia/metas');
    case 'rebalance':
      context.go('/estrategia');
    case 'market':
    default:
      context.go('/descobrir');
  }
}
