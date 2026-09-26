import 'package:flutter_test/flutter_test.dart';
import 'package:fiance/core/models.dart';

Map<String, dynamic> _mes([Map<String, dynamic> extra = const {}]) => {
  'month': '2026-03',
  'category': 'acoes_br',
  'gross_sales': 1200.0,
  'result': 200.0,
  'exempt': false,
  'loss_offset_used': 0.0,
  'taxable_profit': 200.0,
  'ir_rate': 0.2,
  'ir_amount': 40.0,
  'sales': 1,
  'observation': 'Day trade: IR 20% sobre o resultado do mês, sem isenção.',
  ...extra,
};

Map<String, dynamic> _venda([Map<String, dynamic> extra = const {}]) => {
  'id': 2,
  'ticker': 'PETR4',
  'category': 'acoes_br',
  'quantity': 100.0,
  'avg_price': 10.0,
  'sell_price': 12.0,
  'gross_profit': 200.0,
  'ir_rate': 0.2,
  'ir_amount': 40.0,
  'net_profit': 160.0,
  'sold_at': 1773100800.0,
  ...extra,
};

void main() {
  group('apuração de day trade chega ao app sem quebrar quem não a tem', () {
    test('servidor antigo, sem os campos novos, lê como operação comum', () {
      final mes = MonthlyTaxAssessment.fromJson(_mes());
      final venda = ClosedTrade.fromJson(_venda());

      expect(mes.dayTrade, isFalse);
      expect(mes.irPayable, isNull,
          reason: 'sem ir_payable a tela cai em ir_amount, e não num zero inventado');
      expect(mes.irrfWithheld, 0);
      expect(venda.dayTrade, isFalse);
    });

    test('mês de day trade traz o IRRF e o que vai para o DARF', () {
      final mes = MonthlyTaxAssessment.fromJson(_mes({
        'day_trade': true,
        'irrf_withheld': 2.0,
        'irrf_deducted': 2.0,
        'ir_payable': 38.0,
      }));

      expect(mes.dayTrade, isTrue);
      expect(mes.irrfWithheld, 2.0);
      expect(mes.irrfDeducted, 2.0);
      expect(mes.irPayable, 38.0);
      expect(ClosedTrade.fromJson(_venda({'day_trade': true})).dayTrade, isTrue);
    });
  });
}
