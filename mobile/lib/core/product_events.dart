import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_repository.dart';
import 'providers.dart';

class ProductEvents {
  ProductEvents(this._api);

  final ApiRepository _api;

  Future<void> track(String name, {Map<String, Object?> props = const {}}) async {
    try {
      await _api.sendEvents([
        {
          'name': name,
          'props': props,
          'platform': defaultTargetPlatform.name,
          'occurred_at': DateTime.now().millisecondsSinceEpoch / 1000,
        },
      ]);
    } catch (_) {
      return;
    }
  }
}

final productEventsProvider = Provider<ProductEvents>(
  (ref) => ProductEvents(ref.watch(apiRepositoryProvider)),
);

void trackEvent(BuildContext context, String name, {Map<String, Object?> props = const {}}) {
  final ProviderContainer container;
  try {
    container = ProviderScope.containerOf(context, listen: false);
  } catch (_) {
    return;
  }
  container.read(productEventsProvider).track(name, props: props);
}
