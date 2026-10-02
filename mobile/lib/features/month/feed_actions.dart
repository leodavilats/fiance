import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/product_events.dart';

void runFeedAction(BuildContext context, String? action, String? ticker) {
  trackEvent(context, 'feed_item_opened', props: {'source': action ?? 'market'});
  switch (action) {
    case 'analyze':
      if (ticker != null) {
        context.push('/ativo/$ticker');
      } else {
        context.go('/patrimonio');
      }
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
