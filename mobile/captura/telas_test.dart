import 'dart:io';
import 'dart:ui' as ui;

import 'package:dio/dio.dart';
import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/router.dart';
import 'package:fiance/core/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

const _tela = Size(390, 1400);

final _saida = Directory('../build/revisao/telas');
final _fontes = Directory('../build/revisao/.fontes');

enum Estado { conteudo, carregando, falha, isEmpty }

void _ignorarFonteAusente() {
  final anterior = FlutterError.onError;
  FlutterError.onError = (detalhes) {
    final texto = detalhes.exception.toString();
    if (texto.contains('allowRuntimeFetching is false')) return;
    anterior?.call(detalhes);
  };
}

Future<void> _carregarIcones() async {
  final arquivo = File('${_fontes.path}/MaterialIcons-Regular.otf');
  if (!arquivo.existsSync()) return;

  final carga = FontLoader('MaterialIcons')
    ..addFont(Future.value(arquivo.readAsBytesSync().buffer.asByteData()));
  await carga.load();
}

Future<void> _carregarFontes() async {
  GoogleFonts.config.allowRuntimeFetching = false;
  _ignorarFonteAusente();
  await _carregarIcones();

  if (!_fontes.existsSync()) {
    fail(
      'Sem as fontes em ${_fontes.path}. Rode `python tool/revisar_telas.py`, que as baixa antes '
      'de chamar este teste — sem elas o Flutter desenha caixas no lugar do texto, e a imagem '
      'engana quem for avaliá-la.',
    );
  }

  const arquivos = {
    'IBMPlexSans': 'IBMPlexSans-Regular.ttf',
    'SourceSerif4': 'SourceSerif4-Regular.ttf',
  };

  for (final fonte in arquivos.entries) {
    final arquivo = File('${_fontes.path}/${fonte.value}');
    if (!arquivo.existsSync()) fail('fonte ausente: ${arquivo.path}');

    final bytes = arquivo.readAsBytesSync().buffer.asByteData();

    for (final variante in const [
      'regular',
      'italic',
      '100',
      '200',
      '300',
      '500',
      '600',
      '700',
      '800',
      '900',
    ]) {
      final carga = FontLoader('${fonte.key}_$variante')
        ..addFont(Future.value(bytes));
      await carga.load();
    }
  }
}

class _RedeDublada extends Interceptor {
  _RedeDublada(this.estado);

  final Estado estado;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (estado == Estado.carregando) return;

    if (estado == Estado.falha) {
      handler.reject(
        DioException(
          requestOptions: options,
          response: Response<dynamic>(requestOptions: options, statusCode: 503),
          type: DioExceptionType.badResponse,
        ),
      );
      return;
    }

    handler.resolve(
      Response<dynamic>(
        requestOptions: options,
        statusCode: 200,
        data: _resposta(options.path, estado),
      ),
    );
  }
}

dynamic _resposta(String caminho, Estado estado) {
  final isEmpty = estado == Estado.isEmpty;

  if (caminho.contains('/preferences')) {
    return {
      'risk_profile': 'moderate',
      'passive_income_goal': isEmpty ? null : 5000.0,
      'preferred_categories': <String>[],
      'preferred_sectors': <String>[],
      'excluded_tickers': <String>[],
      'density': 'comfortable',
      'desired_yield_stock': 0.06,
      'desired_yield_fii': 0.10,
      'desired_yield_bdr': 0.04,
      'desired_yield_etf': 0.04,
    };
  }

  if (caminho.contains('/auth/me')) {
    return {'id': 'demo', 'name': 'Maria', 'email': 'maria@exemplo.com'};
  }

  // Rotas que devolvem lista crua: no estado sem dado, o cliente espera [] e nao um objeto.
  const listas = [
    '/goals',
    '/sector-goals',
    '/alerts',
    '/cashflow/debts',
    '/cashflow/entries',
  ];
  if (listas.any(caminho.contains)) {
    return isEmpty ? <dynamic>[] : _cheio(caminho);
  }

  // O objeto vazio generico nao tem forma de resposta unica (ex.: 'summary' do
  // dashboard, ou os totais da renda fixa); sem ela o parser do cliente quebra
  // e a tela vazia que o proprio widget ja sabe mostrar nunca aparece.
  if (caminho.contains('/fixed-income') && isEmpty) {
    return {
      ..._vazio(),
      'total_investido': 0.0,
      'total_atual': 0.0,
      'total_rendimento': 0.0,
      'rendimento_pct': 0.0,
      'taxa_media_aa': 0.0,
      'cdi_referencia': 0.0,
      'fonte_taxas': 'bcb',
    };
  }

  if (caminho.contains('/dashboard') && isEmpty) {
    return {
      ..._vazio(),
      'summary': {
        'total_invested': 0.0,
        'total_current': 0.0,
        'total_pnl': 0.0,
        'total_pnl_pct': 0.0,
        'monthly_dividends_estimate': 0.0,
        'passive_income_goal': null,
        'passive_income_progress': null,
        'positions_count': 0,
      },
      'top_buys': <dynamic>[],
      'top_sells': <dynamic>[],
      'alerts': <dynamic>[],
    };
  }

  return isEmpty ? _vazio() : _cheio(caminho);
}

Map<String, dynamic> _vazio() => {
  'items': <dynamic>[],
  'count': 0,
  'entries': <dynamic>[],
  'positions': <dynamic>[],
  'allocations': <dynamic>[],
  'snapshots': <dynamic>[],
  'steps': <dynamic>[],
  'goals': <dynamic>[],
  'suggestions': <dynamic>[],
  'debts': <dynamic>[],
  'months': <dynamic>[],
  'by_month': <dynamic>[],
  'by_ticker': <dynamic>[],
  'allocation_gaps': <dynamic>[],
};

Map<String, dynamic> _posicao(
  String ticker,
  String nome,
  double quantidade,
  double medio,
  double current,
  String veredito,
  String rotulo,
  String categoria,
  String setor,
  double dy,
) {
  final investido = quantidade * medio;
  final valor = quantidade * current;
  return {
    'ticker': ticker,
    'name': nome,
    'asset_type': categoria == 'fiis' ? 'fii' : 'br_stock',
    'quantity': quantidade,
    'avg_price': medio,
    'current_price': current,
    'invested': investido,
    'current_value': valor,
    'pnl': valor - investido,
    'pnl_pct': (valor - investido) / investido * 100,
    'verdict': veredito,
    'label': rotulo,
    'category_resolved': categoria,
    'dividend_yield': dy,
    'sector': setor,
    'as_of': 1789324890.0,
    'reasons': <String>[],
    'confidence': 0.75,
    'data_years': 5,
    'consensus_methods': 3,
    'trend_basis': 'long',
  };
}

dynamic _cheio(String caminho) {
  final base = _vazio();

  if (caminho.contains('/dashboard')) {
    return {
      ...base,
      'summary': {
        'total_invested': 84200.00,
        'total_current': 97430.55,
        'total_pnl': 13230.55,
        'total_pnl_pct': 15.71,
        'monthly_dividends_estimate': 412.80,
        'passive_income_goal': 5000.0,
        'passive_income_progress': 8.26,
        'positions_count': 6,
      },
      'positions': [
        _posicao('PETR4', 'Petróleo Brasileiro', 300, 32.10, 38.42, 'BUY', 'Comprar', 'acoes_br',
            'Energia', 9.8),
        _posicao('BBAS3', 'Banco do Brasil', 400, 21.40, 22.49, 'STRONG_BUY',
            'Comprar com convicção', 'acoes_br', 'Bancos', 11.2),
        _posicao('MXRF11', 'Maxi Renda', 900, 9.80, 9.14, 'HOLD', 'Manter', 'fiis',
            'Fundos imobiliários', 12.8),
        _posicao('WEGE3', 'WEG', 120, 44.10, 51.49, 'UNKNOWN', 'Sem dados suficientes',
            'acoes_br', 'Bens industriais', 1.9),
      ],
      'allocations': [
        {'category': 'acoes_br', 'current_value': 52300.0, 'current_pct': 53.7, 'target_pct': 45.0},
        {'category': 'fiis', 'current_value': 24130.55, 'current_pct': 24.8, 'target_pct': 25.0},
        {'category': 'renda_fixa', 'current_value': 18000.0, 'current_pct': 18.5, 'target_pct': 25.0},
        {'category': 'etfs', 'current_value': 3000.0, 'current_pct': 3.0, 'target_pct': 5.0},
      ],
      'top_buys': <dynamic>[],
      'top_sells': <dynamic>[],
      'alerts': <dynamic>[],
      'health': {
        'score': 68.0,
        'concentration_score': 62.0,
        'sector_concentration_score': 58.0,
        'diversification_score': 74.0,
        'risk_score': 70.0,
        'top_position_ticker': 'PETR4',
        'top_position_pct': 11.8,
        'top_sector': 'Energia',
        'top_sector_pct': 22.4,
        'warnings': <dynamic>[],
      },
      'snapshots': [
        {
          'captured_at': 1782000000,
          'total_invested': 71000.0,
          'total_current': 76200.0,
          'total_pnl': 5200.0,
          'total_pnl_pct': 7.32,
        },
        {
          'captured_at': 1784678400,
          'total_invested': 78400.0,
          'total_current': 85100.0,
          'total_pnl': 6700.0,
          'total_pnl_pct': 8.55,
        },
        {
          'captured_at': 1787356800,
          'total_invested': 84200.0,
          'total_current': 97430.55,
          'total_pnl': 13230.55,
          'total_pnl_pct': 15.71,
        },
      ],
    };
  }

  if (caminho.contains('/fixed-income')) {
    return {
      ...base,
      'items': [
        {
          'id': 1,
          'nome': 'CDB Banco Master',
          'tipo': 'cdb',
          'valor_investido': 10000.0,
          'taxa': 118.0,
          'tipo_taxa': 'pos_fixado',
          'percentual_cdi': 118.0,
          'data_aplicacao': '2025-09-10',
          'vencimento': '2027-09-10',
          'liquidez': 'no_vencimento',
          'isento_ir': false,
          'oculto': false,
          'valor_atual': 11240.30,
          'rendimento_acumulado': 1240.30,
          'rendimento_pct': 12.40,
          'meses_decorridos': 12,
          'taxa_anual_efetiva_pct': 13.2,
          'yield_equivalente_pct': 118.0,
          'valor_no_vencimento': 12680.0,
          'dias_para_vencimento': 361,
          'vencimento_proximo': false,
        },
        {
          'id': 2,
          'nome': 'LCI Inter',
          'tipo': 'lci',
          'valor_investido': 8000.0,
          'taxa': 96.0,
          'tipo_taxa': 'pos_fixado',
          'percentual_cdi': 96.0,
          'data_aplicacao': '2026-01-15',
          'vencimento': '2026-10-05',
          'liquidez': 'no_vencimento',
          'isento_ir': true,
          'oculto': false,
          'valor_atual': 8492.10,
          'rendimento_acumulado': 492.10,
          'rendimento_pct': 6.15,
          'meses_decorridos': 8,
          'taxa_anual_efetiva_pct': 10.7,
          'yield_equivalente_pct': 113.0,
          'valor_no_vencimento': 8610.0,
          'dias_para_vencimento': 20,
          'vencimento_proximo': true,
        },
      ],
      'total_investido': 18000.0,
      'total_atual': 19732.40,
      'total_rendimento': 1732.40,
      'rendimento_pct': 9.62,
      'taxa_media_aa': 12.8,
      'cdi_referencia': 11.15,
      'fonte_taxas': 'bcb',
    };
  }

  if (caminho.contains('/cashflow/month')) {
    return {
      ...base,
      'month': '2026-09',
      'received': 8400.0,
      'paid': 5210.40,
      'committed': 1180.00,
      'free_now': 2009.60,
      'surplus_low': 1109.60,
      'surplus_high': 1609.60,
      'has_range': true,
      'income_baseline': 8400.0,
      'estimate': {
        'base_months': ['2026-06', '2026-07', '2026-08'],
        'expected_low': 1800.0,
        'expected_high': 2300.0,
        'spent_so_far': 1400.0,
        'remaining_low': 400.0,
        'remaining_high': 900.0,
      },
      'due': [
        {
          'id': 11,
          'category': 'moradia',
          'description': 'Aluguel',
          'amount': 1800.0,
          'due_on': '2026-09-25',
        },
        {
          'id': 12,
          'category': 'contas_da_casa',
          'description': 'Luz',
          'amount': 180.0,
          'due_on': '2026-09-28',
        },
      ],
    };
  }

  if (caminho.contains('/cashflow/debts')) {
    return [
        {
          'id': 1,
          'kind': 'rotativo_cartao',
          'description': 'Fatura do cartão',
          'balance': 3200.0,
          'monthly_rate': 14.9,
          'class': 'expensive',
          'reference_monthly': 0.92,
          'reference_source': 'carteira',
          'flip_rate': 0.92,
        },
        {
          'id': 2,
          'kind': 'financiamento_veiculo',
          'description': 'Financiamento do carro',
          'balance': 21000.0,
          'monthly_rate': 0.84,
          'class': 'manageable',
          'reference_monthly': 0.92,
        'reference_source': 'carteira',
        'flip_rate': 0.92,
      },
    ];
  }

  if (caminho.contains('/surplus')) {
    return {
      ...base,
      'month': {
        'month': '2026-09',
        'received': 8400.0,
        'paid': 5210.40,
        'committed': 1180.00,
        'free_now': 2009.60,
        'surplus_low': 1109.60,
        'surplus_high': 1609.60,
        'has_range': true,
        'income_baseline': 8400.0,
        'estimate': {
          'base_months': ['2026-06', '2026-07', '2026-08'],
          'expected_low': 1800.0,
          'expected_high': 2300.0,
          'spent_so_far': 1400.0,
          'remaining_low': 400.0,
          'remaining_high': 900.0,
        },
        'due': <dynamic>[],
      },
      'has_cash': true,
      'cascade': {
        'surplus_low': 1109.60,
        'available_to_invest': 0.0,
        'steps': [
          {
            'order': 1,
            'type': 'debt',
            'amount': 1109.60,
            'reason': 'Fatura do cartão custa 14.90% ao mês. Sua carteira rendeu 0.92% ao mês. '
                'Enquanto essa diferença existir, quitar rende mais que aportar.',
            'falsifier': 'Se a taxa da dívida cair abaixo de 0.92% ao mês, quitar deixa de ser a '
                'prioridade.',
            'reference': 'carteira',
          },
        ],
      },
    };
  }

  if (caminho.contains('/rebalance-suggestions')) {
    return {
      ...base,
      'allocation_gaps': [
        {
          'category': 'renda_fixa',
          'current_pct': 18.5,
          'target_pct': 25.0,
          'gap_pct': -6.5,
          'gap_value': 6330.0,
        },
        {
          'category': 'acoes_br',
          'current_pct': 53.7,
          'target_pct': 45.0,
          'gap_pct': 8.7,
          'gap_value': -8470.0,
        },
      ],
      'items': [
        {
          'ticker': 'WEGE3',
          'name': 'WEG',
          'category': 'acoes_br',
          'verdict': 'SELL',
          'action': 'realocar',
          'current_value': 6178.80,
          'quantity': 120.0,
          'pnl_pct': 16.8,
          'reasons': [
            'Preço atual está 118.0% acima do teto da faixa de preço justo '
                '(R\$ 12,94 a R\$ 23,77).',
            'Categoria acoes_br também está acima da meta de alocação.',
          ],
          'requires_tax_review': true,
          'realocar_para': {
            'ticker': 'BBAS3',
            'name': 'Banco do Brasil',
            'category': 'acoes_br',
            'score': 78.0,
            'verdict': 'STRONG_BUY',
          },
        },
      ],
      'tax_disclaimer': 'Vender pode gerar imposto. O número do mês está na apuração.',
    };
  }

  // O Descobrir nunca teve dublê próprio, e saía vazio até na pasta 'conteudo' -- uma imagem
  // dizendo 'sem oportunidade' sobre a tela que é o coração da aba.
  if (caminho.contains('/opportunities')) {
    return {
      ...base,
      'items': [
        {
          'ticker': 'TAEE11',
          'name': 'Taesa',
          'sector': 'Energia',
          'price': 41.91,
          'fair_price': 103.17,
          'fair_low': 60.32,
          'fair_high': 146.03,
          'margin_of_safety': 0.3052,
          'dividend_yield': 8.64,
          'verdict': 'BUY',
          'label': 'Comprar',
          'basis': 'band',
          'score': 81.0,
          'confidence': 0.6,
          'data_years': 6,
          'consensus_methods': 2,
          'trend_basis': 'long',
          'data_completeness': 1.0,
          'change_percent_day': 0.8,
          'distance_from_52w_high_pct': -12.4,
          'range_52w_position': 0.38,
        },
        {
          'ticker': 'BOVA11',
          'name': 'iShares Ibovespa',
          'sector': null,
          'price': 182.47,
          'fair_price': null,
          'fair_low': null,
          'fair_high': null,
          'margin_of_safety': null,
          'dividend_yield': 1.2,
          'verdict': 'BUY',
          'label': 'Comprar',
          'basis': 'trend',
          'score': 54.0,
          'confidence': 0.35,
          'data_years': 0,
          'consensus_methods': 0,
          'trend_basis': 'long',
          'data_completeness': 0.2,
          'change_percent_day': -0.4,
          'distance_from_52w_high_pct': -3.1,
          'range_52w_position': 0.72,
        },
      ],
      'total_count': 2,
      'universe_size': 412,
      'page': 1,
      'page_size': 30,
      'has_more': false,
    };
  }

  if (caminho.contains('/goals')) {
    return [
      {'category': 'acoes_br', 'target_pct': 45.0, 'target_value': 43843.0, 'declared': true},
      {'category': 'fiis', 'target_pct': 25.0, 'target_value': 24357.0, 'declared': true},
      {'category': 'renda_fixa', 'target_pct': 25.0, 'target_value': 24357.0, 'declared': true},
      {'category': 'etfs', 'target_pct': 5.0, 'target_value': 4871.0, 'declared': true},
    ];
  }

  if (caminho.contains('/sector-goals')) {
    return [
      {'sector': 'Energia', 'target_pct': 20.0, 'declared': true},
      {'sector': 'Bancos', 'target_pct': 15.0, 'declared': true},
    ];
  }

  if (caminho.contains('/alerts')) {
    return [
      {
        'id': 1,
        'ticker': 'PETR4',
        'condition': 'below',
        'target_price': 30.0,
        'note': 'Voltar a comprar',
      },
      {'id': 2, 'ticker': 'MXRF11', 'condition': 'above', 'target_price': 11.0},
    ];
  }

  if (caminho.contains('/whats-new')) {
    return {
      ...base,
      'days_since': 3,
      'captured_at': '2026-09-11',
      'total_invested': 84200.0,
      'total_current': 97430.55,
      'total_pnl': 13230.55,
      'total_pnl_pct': 15.71,
      'items': [
        {
          'kind': 'price',
          'ticker': 'PETR4',
          'title': 'PETR4 subiu 4,2% desde a última visita',
          'detail': 'De R\$ 36,87 para R\$ 38,42.',
        },
        {
          'kind': 'dividend',
          'ticker': 'BBAS3',
          'title': 'BBAS3 anunciou JCP',
          'detail': 'R\$ 0,476 por ação, com crédito em 05/09.',
        },
      ],
    };
  }

  if (caminho.contains('/referral')) {
    return {'code': 'MARIA2026', 'invited': 0, 'credited_until': null};
  }

  if (caminho.contains('/account/deletion-policy')) {
    return {
      'sla_days': 30,
      'removes': [
        'cash_entries',
        'debts',
        'dividends_received',
        'goals',
        'positions',
        'preferences',
        'price_alerts',
        'transactions',
      ],
      'note':
          'A remoção é imediata no banco de produção. O prazo declarado cobre backups e '
          'réplicas, onde o dado ainda pode existir até serem rotacionados. Nada disso está '
          'atrás de plano.',
      'confirmation_phrase': 'EXCLUIR',
    };
  }

  if (caminho.contains('/cashflow/entries')) {
    return [
        {
          'id': 1,
          'kind': 'income',
          'category': 'salario',
          'description': 'Salário',
          'amount': 8400.0,
          'due_on': '2026-09-05',
          'paid_on': '2026-09-05',
        },
        {
          'id': 2,
          'kind': 'expense',
          'category': 'moradia',
          'description': 'Aluguel',
          'amount': 1800.0,
          'due_on': '2026-09-25',
          'paid_on': null,
        },
        {
          'id': 3,
          'kind': 'expense',
          'category': 'mercado',
          'description': 'Compras do mês',
          'amount': 980.40,
        'due_on': '2026-09-08',
        'paid_on': '2026-09-08',
      },
    ];
  }

  if (caminho.contains('/transactions')) {
    return {
      ...base,
      'items': [
        {
          'id': 1,
          'kind': 'buy',
          'symbol': 'PETR4',
          'traded_on': '2026-08-14',
          'quantity': 200.0,
          'price': 38.42,
          'fees': 4.9,
        },
        {
          'id': 2,
          'kind': 'sell',
          'symbol': 'VALE3',
          'traded_on': '2026-07-30',
          'quantity': 50.0,
          'price': 61.10,
          'fees': 4.9,
        },
        {
          'id': 3,
          'kind': 'split',
          'symbol': 'WEGE3',
          'traded_on': '2026-06-12',
          'ratio_from': 1.0,
          'ratio_to': 2.0,
        },
      ],
      'count': 3,
    };
  }

  if (caminho.contains('/dividends/pending')) {
    return {
      'items': [
        {
          'ticker': 'BBAS3',
          'paid_at': '2026-09-05',
          'amount': 142.80,
          'quantity_at_date': 300.0,
          'rate_per_share': 0.476,
          'kind': 'jcp',
          'caveats': ['A quantidade usada é a de hoje, não a da data do crédito.'],
          'quantity_is_current': true,
        },
      ],
      'count': 1,
      'note': 'Sugestões do calendário cruzadas com a sua carteira.',
    };
  }

  if (caminho.contains('/dividends')) {
    return {
      ...base,
      'items': [
        {
          'id': 1,
          'ticker': 'PETR4',
          'paid_at': '2026-08-20',
          'amount': 318.40,
          'kind': 'dividendo',
        },
        {
          'id': 2,
          'ticker': 'MXRF11',
          'paid_at': '2026-08-15',
          'amount': 96.10,
          'kind': 'rendimento',
        },
      ],
      'total_received': 4820.50,
      'received_this_month': 414.50,
      'received_last_12m': 4120.00,
      'monthly_average_12m': 343.33,
      'total_count': 2,
      'by_ticker': [
        {'ticker': 'PETR4', 'total': 2480.0, 'count': 8},
        {'ticker': 'MXRF11', 'total': 1152.0, 'count': 12},
      ],
    };
  }

  return base;
}

Future<void> _capturar(WidgetTester tester, String subpasta, String nome) async {
  final boundary =
      tester.firstRenderObject(find.byType(RepaintBoundary)) as RenderRepaintBoundary;

  ByteData? bytes;
  await tester.runAsync(() async {
    final imagem = await boundary.toImage(pixelRatio: 2);
    bytes = await imagem.toByteData(format: ui.ImageByteFormat.png);
    imagem.dispose();
  });

  if (bytes == null) fail('não foi possível codificar $nome');

  final pasta = Directory('${_saida.path}/$subpasta');
  pasta.createSync(recursive: true);
  File('${pasta.path}/$nome.png').writeAsBytesSync(bytes!.buffer.asUint8List());
}

Future<void> _montar(
  WidgetTester tester,
  String rota, {
  required Brightness brilho,
  Estado estado = Estado.conteudo,
}) async {
  tester.view.physicalSize = _tela * 2;
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);

  final dio = Dio()..interceptors.add(_RedeDublada(estado));

  final roteador = GoRouter(initialLocation: rota, routes: appRouter.configuration.routes);

  await tester.pumpWidget(
    RepaintBoundary(
      child: ProviderScope(
        overrides: [apiRepositoryProvider.overrideWithValue(ApiRepository(dio))],
        child: MaterialApp.router(
          debugShowCheckedModeBanner: false,
          theme: buildAppTheme(Brightness.light),
          darkTheme: buildAppTheme(Brightness.dark),
          themeMode: brilho == Brightness.dark ? ThemeMode.dark : ThemeMode.light,
          routerConfig: roteador,
        ),
      ),
    ),
  );

  // Cada Future do Riverpod resolve num ciclo; telas com providers aninhados precisam de mais
  // de um. pumpAndSettle nao serve: o esqueleto de carregamento anima para sempre.
  for (var i = 0; i < 8; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }

  // O google_fonts lanca a cada peso que nao esta nos assets, e o plugin de notificacao nao tem
  // implementacao de plataforma sob flutter test. As duas sao ruido do ambiente: consumidas, o
  // teste segue e a imagem sai. Qualquer outra excecao continua derrubando o teste.
  while (true) {
    final excecao = tester.takeException();
    if (excecao == null) break;
    final texto = excecao.toString();
    if (texto.contains('allowRuntimeFetching')) continue;
    if (texto.contains('LateInitializationError')) continue;
    throw excecao as Object;
  }
}

void main() {
  setUpAll(_carregarFontes);

  const telas = <String, String>{
    'login': '/login',
    'mes': '/mes',
    'mes-atividade': '/mes/atividade',
    'mes-dividas': '/mes/dividas',
    'sobra': '/sobra',
    'sobra-desvio': '/sobra/desvio',
    'patrimonio': '/patrimonio',
    'patrimonio-renda-fixa': '/patrimonio/renda-fixa',
    'patrimonio-razao': '/patrimonio/razao',
    'patrimonio-proventos': '/patrimonio/proventos',
    'descobrir': '/descobrir',
    'voce': '/voce',
    'voce-objetivos': '/voce/objetivos',
    'voce-conta': '/voce/conta',
    'voce-conta-excluir': '/voce/conta/excluir',
  };

  for (final screen in telas.entries) {
    for (final estado in Estado.values) {
      for (final brilho in const [Brightness.light, Brightness.dark]) {
        final tema = brilho == Brightness.light ? 'claro' : 'escuro';

        testWidgets('${screen.key} - ${estado.name} - $tema', (tester) async {
          await _montar(tester, screen.value, brilho: brilho, estado: estado);
          await _capturar(tester, estado.name, '${screen.key}-$tema');
        });
      }
    }
  }
}
