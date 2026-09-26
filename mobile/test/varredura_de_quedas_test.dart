import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/models.dart';

void main() {
  test('o item da varredura traz a leitura de valor, e não uma nota própria de queda', () {
    final item = DipScanItem.fromJson({
      'symbol': 'VALE3',
      'name': 'Vale ON',
      'price': 60.0,
      'as_of': 1790000000.0,
      'drop_from_52w_high_pct': 14.29,
      'verdict': 'HOLD',
      'label': 'No preço justo',
      'fair_low': 55.0,
      'fair_high': 72.0,
      'margin_of_safety': 0.0,
      'top_reason': 'O preço está dentro da faixa de preço justo.',
    });

    expect(item.label, 'No preço justo');
    expect(item.verdict, 'HOLD');
    expect(item.dropFromHighPct, 14.29);
    expect(item.asOf, 1790000000.0, reason: 'preço em lista vem com o carimbo de quando foi lido');
  });
}
