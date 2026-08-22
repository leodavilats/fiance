import 'package:dio/dio.dart';
import 'package:fiance/core/models.dart';
import 'package:fiance/core/widgets/error_state.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('RebalanceSuggestions', () {
    test('não descarta allocation_gaps', () {
      final json = {
        'allocation_gaps': [
          {
            'category': 'fiis',
            'target_pct': 25.0,
            'current_pct': 18.0,
            'gap_pct': 7.0,
            'target_value': 25000.0,
            'current_value': 18000.0,
            'gap_value': 7000.0,
            'action': 'comprar',
          },
        ],
        'items': [],
        'tax_disclaimer': null,
      };

      final parsed = RebalanceSuggestions.fromJson(json);

      expect(parsed.allocationGaps, hasLength(1));
      expect(parsed.allocationGaps.first.category, 'fiis');
      expect(parsed.allocationGaps.first.gapPct, 7.0);
      expect(parsed.allocationGaps.first.isBelowTarget, isTrue);
    });

    test('biggestGap usa o maior desvio em módulo, não o maior positivo', () {
      final parsed = RebalanceSuggestions.fromJson({
        'allocation_gaps': [
          {'category': 'fiis', 'gap_pct': 4.0},
          {'category': 'acoes_br', 'gap_pct': -9.0},
          {'category': 'renda_fixa', 'gap_pct': 0.0},
        ],
        'items': [],
      });

      expect(parsed.biggestGap!.category, 'acoes_br');
      expect(parsed.biggestGap!.isBelowTarget, isFalse);
    });

    test('biggestGap é nulo sem metas definidas', () {
      final parsed = RebalanceSuggestions.fromJson({'allocation_gaps': [], 'items': []});
      expect(parsed.biggestGap, isNull);
    });
  });

  group('fiErrorMessage', () {
    test('distingue rede caída de sessão expirada', () {
      final offline = DioException(
        requestOptions: RequestOptions(),
        type: DioExceptionType.connectionError,
      );
      expect(fiErrorMessage(offline), contains('Sem conexão'));

      final expired = DioException(
        requestOptions: RequestOptions(),
        response: Response(requestOptions: RequestOptions(), statusCode: 401),
      );
      expect(fiErrorMessage(expired), contains('sessão expirou'));
    });

    test('usa o detail do backend quando ele existe', () {
      final domain = DioException(
        requestOptions: RequestOptions(),
        response: Response(
          requestOptions: RequestOptions(),
          statusCode: 409,
          data: {'detail': 'Quantidade maior que a posição.'},
        ),
      );
      expect(fiErrorMessage(domain), 'Quantidade maior que a posição.');
    });

    test('nunca vaza a exceção crua', () {
      final message = fiErrorMessage(StateError('boom interno'), action: 'salvar');
      expect(message, isNot(contains('boom interno')));
      expect(message, contains('salvar'));
    });
  });
}
