import 'package:dio/dio.dart';
import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/month.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/error_state.dart';
import 'package:fiance/features/month/activity_screen.dart';
import 'package:fiance/features/month/debts_screen.dart';
import 'package:fiance/features/month/month_screen.dart';
import 'package:fiance/features/surplus/allocation_drift_screen.dart';
import 'package:fiance/features/surplus/surplus_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

typedef _Rota = ({int status, Object? data});

class _Servidor extends Interceptor {
  _Servidor(this.rotas);

  final Map<String, _Rota> rotas;
  final pedidos = <String>[];

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final chave = '${options.method} ${options.path}';
    pedidos.add(chave);
    final r = rotas[chave] ?? (status: 404, data: {'detail': 'sem dado neste teste'});
    final resposta = Response<dynamic>(
      requestOptions: options,
      statusCode: r.status,
      data: r.data,
    );
    if (r.status >= 400) {
      handler.reject(
        DioException(
          requestOptions: options,
          response: resposta,
          type: DioExceptionType.badResponse,
        ),
      );
      return;
    }
    handler.resolve(resposta);
  }
}

final _mes = currentMonth();

Map<String, dynamic> _cashMonth({List<Map<String, dynamic>> due = const []}) => {
  'month': _mes,
  'received': 10000.0,
  'paid': 1000.0,
  'committed': 1400.0,
  'free_now': 7600.0,
  'surplus_low': 7000.0,
  'surplus_high': 7600.0,
  'has_range': true,
  'income_baseline': 10000.0,
  'estimate': {'base_months': <String>[previousMonth(_mes)]},
  'due': due,
};

Map<String, dynamic> _entrada({
  int id = 1,
  String kind = 'expense',
  String description = 'Aluguel',
  String? paidOn,
}) => {
  'id': id,
  'kind': kind,
  'category': kind == 'income' ? 'salario' : 'moradia',
  'description': description,
  'amount': 1400.0,
  'due_on': '$_mes-10',
  'paid_on': paidOn,
  'derived': false,
};

Future<_Servidor> _abrir(
  WidgetTester tester,
  Widget tela,
  Map<String, _Rota> rotas,
) async {
  tester.view.physicalSize = const Size(390, 2400) * 2;
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);

  final servidor = _Servidor(rotas);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        apiRepositoryProvider.overrideWithValue(
          ApiRepository(Dio()..interceptors.add(servidor)),
        ),
      ],
      child: MaterialApp(theme: buildAppTheme(Brightness.light), home: tela),
    ),
  );
  await _esperar(tester);
  return servidor;
}

Future<void> _esperar(WidgetTester tester) async {
  for (var i = 0; i < 8; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }
}

String _capitalizado(String t) => '${t[0].toUpperCase()}${t.substring(1)}';

void main() {
  group('/mes', () {
    testWidgets('falha ao ler os lançamentos não vira mês vazio', (tester) async {
      await _abrir(tester, const MonthScreen(), {
        'GET /cashflow/month': (status: 200, data: _cashMonth()),
        'GET /cashflow/entries': (status: 500, data: {'detail': 'fora do ar'}),
        'GET /cashflow/debts': (status: 200, data: <Object>[]),
      });

      expect(
        find.text('Seu mês ainda não tem nada lançado'),
        findsNothing,
        reason: 'ausência de dado e falha de leitura nunca compartilham a mesma tela',
      );
      expect(
        find.byType(FiErrorState),
        findsOneWidget,
        reason: 'a falha dos lançamentos tem que aparecer como falha, com tentar de novo',
      );
    });

    testWidgets('falha ao ler as dívidas não dá veredito sem a dívida cara', (tester) async {
      await _abrir(tester, const MonthScreen(), {
        'GET /cashflow/month': (status: 200, data: _cashMonth()),
        'GET /cashflow/entries': (status: 200, data: [_entrada(paidOn: '$_mes-05')]),
        'GET /cashflow/debts': (status: 500, data: {'detail': 'fora do ar'}),
      });

      expect(find.byType(FiErrorState), findsOneWidget);
      expect(
        find.text('Mês folgado'),
        findsNothing,
        reason: 'sem as dívidas, um veredito favorável esconderia a dívida cara',
      );
    });

    testWidgets('a tela diz qual mês está em leitura, e o nome troca de mês', (tester) async {
      await _abrir(tester, const MonthScreen(), {
        'GET /cashflow/month': (status: 200, data: _cashMonth()),
        'GET /cashflow/entries': (status: 200, data: [_entrada(paidOn: '$_mes-05')]),
        'GET /cashflow/debts': (status: 200, data: <Object>[]),
      });

      final nome = _capitalizado(monthName(_mes));
      expect(find.text(nome), findsOneWidget, reason: 'o mês em leitura precisa estar escrito');

      await tester.tap(find.text(nome));
      await _esperar(tester);

      expect(
        find.text(_capitalizado(monthName(nextMonth(_mes)))),
        findsOneWidget,
        reason: 'o seletor oferece o mês seguinte, para lançar o que já se sabe que vem',
      );
    });

    testWidgets('marcar paga avisa e oferece desfazer', (tester) async {
      final servidor = await _abrir(tester, const MonthScreen(), {
        'GET /cashflow/month': (
          status: 200,
          data: _cashMonth(
            due: [
              {
                'id': 1,
                'category': 'moradia',
                'description': 'Aluguel',
                'amount': 1400.0,
                'due_on': '$_mes-10',
              },
            ],
          ),
        ),
        'GET /cashflow/entries': (status: 200, data: [_entrada()]),
        'GET /cashflow/debts': (status: 200, data: <Object>[]),
        'POST /cashflow/entries/1/paid': (status: 204, data: null),
        'PUT /cashflow/entries/1': (status: 200, data: _entrada()),
      });

      await tester.tap(find.text('Marcar paga'));
      await _esperar(tester);

      expect(servidor.pedidos, contains('POST /cashflow/entries/1/paid'));
      expect(find.text('Conta marcada como paga'), findsOneWidget);
      expect(
        find.text('Desfazer'),
        findsOneWidget,
        reason: 'um toque errado em "Marcar paga" precisa ter volta',
      );

      await tester.tap(find.text('Desfazer'));
      await _esperar(tester);
      expect(
        servidor.pedidos,
        contains('PUT /cashflow/entries/1'),
        reason: 'desfazer devolve a conta para a vencer pela porta de edição',
      );
    });
  });

  group('/mes vazio', () {
    testWidgets('uma ação principal só, e ela abre o que a frase pede', (tester) async {
      await _abrir(tester, const MonthScreen(), {
        'GET /cashflow/month': (status: 200, data: _cashMonth()),
        'GET /cashflow/entries': (status: 200, data: <Object>[]),
        'GET /cashflow/debts': (status: 200, data: <Object>[]),
      });

      expect(
        find.byType(FloatingActionButton),
        findsNothing,
        reason: 'no mês vazio o botão do estado vazio já é a ação principal: duas iguais confundem',
      );

      await tester.tap(find.text('Lançar o que você recebe'));
      await _esperar(tester);

      expect(
        find.text('Dia do crédito'),
        findsOneWidget,
        reason: 'a frase pede para começar pelo que você recebe, então a folha abre em Entrada',
      );
    });

    testWidgets('mês seguinte não diz que sobrou', (tester) async {
      await _abrir(tester, const MonthScreen(), {
        'GET /cashflow/month': (status: 200, data: _cashMonth()),
        'GET /cashflow/entries': (status: 200, data: [_entrada(paidOn: '$_mes-05')]),
        'GET /cashflow/debts': (status: 200, data: <Object>[]),
      });

      await tester.tap(find.text(_capitalizado(monthName(_mes))));
      await _esperar(tester);
      await tester.tap(find.text(_capitalizado(monthName(nextMonth(_mes)))));
      await _esperar(tester);

      expect(
        find.textContaining('SOBROU EM'),
        findsNothing,
        reason: 'um mês que ainda não começou não tem sobra fechada para afirmar no passado',
      );
      expect(find.textContaining('PELO QUE ESTÁ LANÇADO'), findsOneWidget);
    });
  });

  group('/mes/dividas', () {
    testWidgets('sem taxa nenhuma, o veredito não diz que a dívida é barata', (tester) async {
      await _abrir(tester, const DebtsScreen(), {
        'GET /cashflow/debts': (
          status: 200,
          data: [
            {
              'id': 1,
              'kind': 'rotativo_cartao',
              'description': 'Fatura do cartão',
              'balance': 3200.0,
              'monthly_rate': null,
              'class': 'no_rate',
              'reference_monthly': null,
              'reference_source': 'sem_taxa_informada',
              'flip_rate': null,
            },
          ],
        ),
      });

      expect(
        find.textContaining('Nenhuma dívida sua custa mais'),
        findsNothing,
        reason: 'sem taxa não há classe: afirmar que nenhuma é cara é julgar sem comparação',
      );
      expect(find.text('Sem a taxa, não dá para dizer se suas dívidas são caras.'), findsOneWidget);
    });
  });

  group('/mes/atividade', () {
    testWidgets('sem novidade mostra o estado vazio', (tester) async {
      await _abrir(tester, const ActivityScreen(), {
        'GET /whats-new': (
          status: 200,
          data: {
            'items': [
              {
                'kind': 'empty',
                'severity': 'info',
                'title': 'Nada de novo por aqui',
                'detail': '',
                'action': '/descobrir',
                'action_label': 'Ver oportunidades',
              },
            ],
          },
        ),
      });

      expect(
        find.text('Nada mudou desde a sua última visita'),
        findsOneWidget,
        reason: 'o servidor manda um item "empty" quando não há novidade: ele não é novidade',
      );
      expect(find.textContaining('do mais recente para o mais antigo'), findsNothing);
    });
  });

  group('/sobra', () {
    testWidgets('mês no vermelho não fala de passo que não existe', (tester) async {
      await _abrir(tester, const SurplusScreen(), {
        'GET /surplus': (
          status: 200,
          data: {
            'month': {
              ..._cashMonth(),
              'free_now': -300.0,
              'surplus_low': -800.0,
              'surplus_high': -300.0,
            },
            'has_cash': true,
            'cascade': {'surplus_low': -800.0, 'available_to_invest': 0.0, 'steps': <Object>[]},
          },
        ),
      });

      expect(
        find.textContaining('o que está acima'),
        findsNothing,
        reason: 'sem passo nenhum, não há nada acima para a frase apontar',
      );
      expect(find.textContaining('não há o que distribuir'), findsOneWidget);
      expect(find.text('Ver o Mês'), findsOneWidget);
    });

    testWidgets('a faixa da manchete não pendura traço na quebra', (tester) async {
      await _abrir(tester, const SurplusScreen(), {
        'GET /surplus': (
          status: 200,
          data: {
            'month': _cashMonth(),
            'has_cash': true,
            'cascade': {'surplus_low': 7000.0, 'available_to_invest': 0.0, 'steps': <Object>[]},
          },
        ),
      });

      expect(find.textContaining(' — R\$'), findsNothing, reason: 'o leitor de tela lia "traço"');
      expect(find.textContaining(' a\u00A0R\$'), findsOneWidget);
    });
  });

  group('/sobra/desvio', () {
    testWidgets('dentro da meta não há maior desvio a nomear', (tester) async {
      await _abrir(tester, const AllocationDriftScreen(), {
        'GET /rebalance-suggestions': (
          status: 200,
          data: {
            'allocation_gaps': [
              {'category': 'acoes_br', 'target_pct': 50.0, 'current_pct': 51.5, 'gap_pct': -1.5},
              {'category': 'fiis', 'target_pct': 50.0, 'current_pct': 48.5, 'gap_pct': 1.5},
            ],
            'items': <Object>[],
          },
        ),
      });

      expect(
        find.textContaining('Seu maior desvio'),
        findsNothing,
        reason: 'um desvio abaixo de $fiRelevantGapPp p.p. é "dentro da meta" na linha, e a '
            'leitura não pode contradizê-la',
      );
      expect(find.textContaining('não há desvio que peça ajuste'), findsOneWidget);
    });

    testWidgets('meta declarada sem carteira não vira "não declarou metas"', (tester) async {
      await _abrir(tester, const AllocationDriftScreen(), {
        'GET /rebalance-suggestions': (
          status: 200,
          data: {'allocation_gaps': <Object>[], 'items': <Object>[]},
        ),
        'GET /goals': (
          status: 200,
          data: [
            {'category': 'acoes_br', 'target_pct': 60.0, 'declared': true},
            {'category': 'renda_fixa', 'target_pct': 40.0, 'declared': true},
          ],
        ),
      });

      expect(
        find.text('Você ainda não declarou metas de alocação'),
        findsNothing,
        reason: 'quem declarou metas e ainda não tem posição não pode ler que não declarou',
      );
      expect(find.text('Ainda não há carteira para comparar com as metas'), findsOneWidget);
    });

    testWidgets('sem meta declarada, o vazio pede a declaração', (tester) async {
      await _abrir(tester, const AllocationDriftScreen(), {
        'GET /rebalance-suggestions': (
          status: 200,
          data: {'allocation_gaps': <Object>[], 'items': <Object>[]},
        ),
        'GET /goals': (
          status: 200,
          data: [
            {'category': 'acoes_br', 'target_pct': 0.0, 'declared': false},
          ],
        ),
      });

      expect(find.text('Você ainda não declarou metas de alocação'), findsOneWidget);
    });

    testWidgets('falha ao ler as metas não vira "não declarou metas"', (tester) async {
      await _abrir(tester, const AllocationDriftScreen(), {
        'GET /rebalance-suggestions': (
          status: 200,
          data: {'allocation_gaps': <Object>[], 'items': <Object>[]},
        ),
        'GET /goals': (status: 500, data: {'detail': 'fora do ar'}),
      });

      expect(
        find.text('Você ainda não declarou metas de alocação'),
        findsNothing,
        reason: 'falha e vazio nunca compartilham a mesma tela',
      );
      expect(find.byType(FiErrorState), findsOneWidget);
    });

    testWidgets('a etiqueta da posição descreve posição, não ordem', (tester) async {
      await _abrir(tester, const AllocationDriftScreen(), {
        'GET /rebalance-suggestions': (
          status: 200,
          data: {
            'allocation_gaps': [
              {'category': 'acoes_br', 'target_pct': 45.0, 'current_pct': 53.7, 'gap_pct': -8.7},
              {'category': 'renda_fixa', 'target_pct': 25.0, 'current_pct': 18.5, 'gap_pct': 6.5},
            ],
            'items': [
              {'ticker': 'WEGE3', 'category': 'acoes_br', 'action': 'realocar', 'reasons': <Object>[]},
              {'ticker': 'ITSA4', 'category': 'acoes_br', 'action': 'manter', 'reasons': <Object>[]},
            ],
          },
        ),
      });

      expect(find.text('Realocar'), findsNothing, reason: 'a etiqueta descreve posição, nunca ordem');
      expect(find.text('Manter'), findsNothing, reason: 'a etiqueta descreve posição, nunca ordem');
      expect(find.text('Acima do preço justo'), findsOneWidget);
      expect(find.text('Sem ajuste'), findsOneWidget);
      expect(
        find.text('faltam 6,5 p.p. para a meta'),
        findsOneWidget,
        reason: 'o desvio e os percentuais da linha precisam fechar na mesma precisão',
      );
      expect(find.textContaining('18,5% de 25%', findRichText: true), findsOneWidget);
    });
  });
}
