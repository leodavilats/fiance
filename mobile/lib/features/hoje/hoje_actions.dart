import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

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
