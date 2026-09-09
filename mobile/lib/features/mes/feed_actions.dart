import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

void runHojeAction(BuildContext context, String? action, String? ticker) {
  switch (action) {
    case 'analyze':
      context.go(ticker != null ? '/ativo/$ticker' : '/patrimonio');
    case 'sell':
      context.go('/patrimonio');
    case 'fixed_income':
      context.go('/patrimonio/renda-fixa');
    case 'goals':
      context.go('/voce/objetivos');
    case 'rebalance':
      context.go('/sobra/desvio');
    case 'market':
    default:
      context.go('/descobrir');
  }
}
